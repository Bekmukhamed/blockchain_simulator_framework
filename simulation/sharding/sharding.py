import random
import math
from collections import defaultdict, deque
from typing import List, Dict, Tuple, Optional
import simulation.globals as sim_globals


class ShardMetrics:    
    def __init__(self, shard_id: int):
        self.shard_id = shard_id
        self.transaction_count = 0
        self.cross_shard_tx_count = 0
        self.processing_time = 0.0
        self.node_count = 0
        self.avg_latency = 0.0
        
        # Recent activity (10 blocks)
        self.tx_history = deque(maxlen=10)
        self.latency_history = deque(maxlen=10)
        self.load_history = deque(maxlen=10)
    
    def update_metrics(self, tx_count: int, cross_shard_tx: int, latency: float):
        self.transaction_count += tx_count
        self.cross_shard_tx_count += cross_shard_tx
        
        self.tx_history.append(tx_count)
        # Skip latency tracking for speed - only used for reporting
        # self.latency_history.append(latency)
        
        # Calculate load as tx_count / node_count
        load = tx_count / max(self.node_count, 1)
        self.load_history.append(load)
        
        # Skip expensive averaging calculation - calculate on demand
        # if self.tx_history:
        #     self.avg_latency = sum(self.latency_history) / len(self.latency_history)
    
    def get_average_load(self) -> float:
        if not self.load_history:
            return 0.0
        return sum(self.load_history) / len(self.load_history)
    
    def get_cross_shard_ratio(self) -> float:
        if self.transaction_count == 0:
            return 0.0
        return self.cross_shard_tx_count / self.transaction_count
    
    def is_overloaded(self, threshold: float = 80.0) -> bool:
        return self.get_average_load() > threshold
    
    def is_underloaded(self, threshold: float = 20.0) -> bool:
        return self.get_average_load() < threshold


class DynamicShardManager:    
    def __init__(self, initial_shard_count: int = 4, max_shards: int = 16):
        self.shard_count = initial_shard_count
        self.max_shards = max_shards
        self.min_shards = 2
        
        # Shard assignment for wallet addresses  
        self.wallet_to_shard: Dict[int, int] = {}
        
        # Shard metrics tracking
        self.shard_metrics: Dict[int, ShardMetrics] = {}
        for i in range(self.shard_count):
            self.shard_metrics[i] = ShardMetrics(i)
        
        # Node assignment: node_id -> shard_id
        self.node_to_shard: Dict[int, int] = {}
        
        # Adaptation parameters
        self.load_threshold_high = 80.0  # Split shard if load > 80%
        self.load_threshold_low = 20.0   # Merge shard if load < 20%
        self.cross_shard_threshold = 0.3  # Reorganize if >30% cross-shard tx (set to 1.0 to disable)
        
        # Performance optimization flags
        self.fast_mode = False  # Set to True to disable cross-shard tracking entirely
        self.skip_adaptation = False  # Set to True to disable dynamic adaptation for max speed
        
        # Cache for wallet assignments to avoid repeated dictionary lookups
        self._wallet_cache_size = 1000
        self._last_cache_clear = 0
        
        # Adaptation cooldown (prevent rapid changes)
        self.last_adaptation_block = -999  # Start with old value so first check works
        self.adaptation_cooldown = 5  # blocks
        
        # Performance tracking
        self.total_adaptations = 0
        self.adaptation_count = 0  # Track total adaptations for reporting
        self.adaptation_history = []
    
    def assign_nodes_to_shards(self, nodes: List) -> None:
        """Initial assignment of nodes to shards"""
        nodes_per_shard = len(nodes) // self.shard_count
        
        for i, node in enumerate(nodes):
            shard_id = i // nodes_per_shard
            if shard_id >= self.shard_count:
                shard_id = self.shard_count - 1
            
            self.node_to_shard[node.id] = shard_id
            self.shard_metrics[shard_id].node_count += 1
            
            # Add shard_id attribute to existing node
            node.shard_id = shard_id
    
    def enable_fast_mode(self, enabled: bool = True):
        """Enable fast mode to skip expensive tracking for maximum speed"""
        self.fast_mode = enabled
        if enabled:
            print("Fast mode enabled: Cross-shard tracking disabled for maximum speed")
    
    def enable_turbo_mode(self, enabled: bool = True):
        """Enable turbo mode: disables both cross-shard tracking AND dynamic adaptation"""
        self.fast_mode = enabled
        self.skip_adaptation = enabled
        if enabled:
            print("Turbo mode enabled: All expensive operations disabled for maximum speed")
            print("Sharding will use static configuration only")
    
    def get_shard_for_wallet(self, wallet_id: int) -> int:
        """Get shard assignment for a wallet using optimized hashing"""
        # Fast path - check cache first
        cached_shard = self.wallet_to_shard.get(wallet_id)
        if cached_shard is not None and cached_shard in self.shard_metrics:
            return cached_shard
        
        # Use simplified modulo assignment for speed
        shard_id = wallet_id % self.shard_count
        
        self.wallet_to_shard[wallet_id] = shard_id
        return shard_id
    
    def route_transaction(self, tx_tuple) -> Tuple[int, bool]:
        """
        Route transaction using existing transaction format (wallet_id, timestamp)
        Returns: (target_shard_id, is_cross_shard)
        Optimized for speed
        """
        # tx_tuple format: (sender_wallet_id, timestamp)
        sender_wallet = tx_tuple[0]
        
        sender_shard = self.get_shard_for_wallet(sender_wallet)
        
        # Skip cross-shard calculation for speed if not needed
        if self.fast_mode or self.cross_shard_threshold >= 1.0:
            return sender_shard, False
        
        # For simplicity, assume receiver is a random wallet
        # In a real implementation, you'd extract this from transaction details
        receiver_wallet = (sender_wallet + 1) % 1000  # Simple pattern instead of random
        receiver_shard = self.get_shard_for_wallet(receiver_wallet)
        
        # Process transaction in the sender's shard
        is_cross_shard = sender_shard != receiver_shard
        
        return sender_shard, is_cross_shard
    
    def process_block(self, block, block_time: float = 1.0) -> None:
        """Process a block and update shard metrics - highly optimized version"""
        # Process transactions from the block
        tx_count = getattr(block, 'tx', 0)
        if tx_count <= 0 or not sim_globals.pool:
            # No transactions to process, just update with zeros
            for metrics in self.shard_metrics.values():
                metrics.update_metrics(0, 0, block_time)
            return
        
        # Fast path for simple load distribution (no cross-shard tracking)
        if self.fast_mode:
            # Distribute transactions evenly across shards for speed
            tx_per_shard = tx_count // self.shard_count
            remainder = tx_count % self.shard_count
            
            for i, metrics in enumerate(self.shard_metrics.values()):
                shard_tx = tx_per_shard + (1 if i < remainder else 0)
                metrics.update_metrics(shard_tx, 0, block_time)
            return
        
        # Standard processing with transaction routing
        shard_tx_count = [0] * self.shard_count  # Use list instead of dict for speed
        shard_cross_tx_count = [0] * self.shard_count
        
        transactions_to_process = sim_globals.pool[:tx_count]
        
        for tx_tuple in transactions_to_process:
            sender_wallet = tx_tuple[0]
            shard_id = sender_wallet % self.shard_count  # Direct calculation, skip method call
            shard_tx_count[shard_id] += 1
            
            # Only calculate cross-shard if needed
            if not self.fast_mode and self.cross_shard_threshold < 1.0:
                receiver_wallet = (sender_wallet + 1) % 1000
                receiver_shard = receiver_wallet % self.shard_count
                if shard_id != receiver_shard:
                    shard_cross_tx_count[shard_id] += 1
        
        # Update metrics for existing shards
        for i, metrics in enumerate(self.shard_metrics.values()):
            metrics.update_metrics(shard_tx_count[i], shard_cross_tx_count[i], block_time)
    
    def should_adapt(self, current_block: int) -> bool:
        """Check if adaptation should occur - optimized"""
        if current_block - self.last_adaptation_block < self.adaptation_cooldown:
            return False
        
        # Quick check - only evaluate if we have enough history
        if not any(len(metrics.load_history) >= 3 for metrics in self.shard_metrics.values()):
            return False
        
        # Check if any shard needs adaptation
        for metrics in self.shard_metrics.values():
            if len(metrics.load_history) >= 3:  # Only check if we have some history
                avg_load = sum(metrics.load_history) / len(metrics.load_history)
                if avg_load > self.load_threshold_high:
                    return True
                if avg_load < self.load_threshold_low and self.shard_count > self.min_shards:
                    return True
                # Skip expensive cross-shard ratio calculation unless needed
                if self.cross_shard_threshold < 1.0 and metrics.get_cross_shard_ratio() > self.cross_shard_threshold:
                    return True
        
        return False
    
    def adapt_shards(self, current_block: int, nodes: List) -> Dict[str, any]:
        """
        Adapt shard configuration based on current metrics
        Works with existing Node objects
        """
        # Fast exit if adaptation is disabled
        if self.skip_adaptation or not self.should_adapt(current_block):
            return {"action": "none"}
        
        self.last_adaptation_block = current_block
        
        # Use cached load calculations instead of recalculating
        overloaded_shards = []
        underloaded_shards = []
        
        for shard_id, metrics in self.shard_metrics.items():
            if len(metrics.load_history) >= 3:
                avg_load = sum(metrics.load_history) / len(metrics.load_history)
                if avg_load > self.load_threshold_high:
                    overloaded_shards.append(shard_id)
                elif avg_load < self.load_threshold_low:
                    underloaded_shards.append(shard_id)
        
        # Adaptation logic
        adaptation_result = {"action": "none"}
        
        if overloaded_shards and self.shard_count < self.max_shards:
            adaptation_result = self._split_shard(overloaded_shards[0], nodes)
        elif len(underloaded_shards) >= 2 and self.shard_count > self.min_shards:
            adaptation_result = self._merge_shards(underloaded_shards[0], underloaded_shards[1], nodes)
        else:
            adaptation_result = self._rebalance_shards(nodes)
        
        if adaptation_result["action"] != "none":
            self.total_adaptations += 1
            self.adaptation_count += 1  # Update both counters for consistency
            self.adaptation_history.append({
                "block": current_block,
                "action": adaptation_result["action"],
                "details": adaptation_result
            })
        
        return adaptation_result
    
    def _split_shard(self, shard_id: int, nodes: List) -> Dict[str, any]:
        """Split an overloaded shard into two"""
        if self.shard_count >= self.max_shards:
            return {"action": "split_failed", "reason": "max_shards_reached"}
        
        new_shard_id = self.shard_count
        self.shard_count += 1
        self.shard_metrics[new_shard_id] = ShardMetrics(new_shard_id)
        
        # Move half the nodes from old shard to new shard
        nodes_in_shard = [node for node in nodes if self.node_to_shard.get(node.id) == shard_id]
        nodes_to_move = nodes_in_shard[len(nodes_in_shard)//2:]
        
        for node in nodes_to_move:
            self.node_to_shard[node.id] = new_shard_id
            node.shard_id = new_shard_id
            self.shard_metrics[shard_id].node_count -= 1
            self.shard_metrics[new_shard_id].node_count += 1
        
        # Reassign some wallets to new shard - simplified approach
        wallets_to_reassign = []
        for wallet_id, current_shard in self.wallet_to_shard.items():
            if current_shard == shard_id and wallet_id % 2 == 0:  # Faster than hash()
                wallets_to_reassign.append(wallet_id)
        
        for wallet_id in wallets_to_reassign:
            self.wallet_to_shard[wallet_id] = new_shard_id
        
        return {
            "action": "split",
            "old_shard": shard_id,
            "new_shard": new_shard_id,
            "nodes_moved": len(nodes_to_move),
            "wallets_reassigned": len(wallets_to_reassign)
        }
    
    def _merge_shards(self, shard1: int, shard2: int, nodes: List) -> Dict[str, any]:
        """Merge two underloaded shards"""
        if self.shard_count <= self.min_shards:
            return {"action": "merge_failed", "reason": "min_shards_reached"}
        
        # Move all resources from shard2 to shard1
        nodes_moved = 0
        for node in nodes:
            if self.node_to_shard.get(node.id) == shard2:
                self.node_to_shard[node.id] = shard1
                node.shard_id = shard1
                nodes_moved += 1
        
        # Reassign wallets
        wallets_reassigned = 0
        for wallet_id, current_shard in list(self.wallet_to_shard.items()):
            if current_shard == shard2:
                self.wallet_to_shard[wallet_id] = shard1
                wallets_reassigned += 1
        
        # Update metrics
        self.shard_metrics[shard1].node_count += self.shard_metrics[shard2].node_count
        del self.shard_metrics[shard2]
        
        # Renumber shards to fill the gap
        self._renumber_shards(shard2, nodes)
        
        self.shard_count -= 1
        
        return {
            "action": "merge",
            "shard1": shard1,
            "shard2": shard2,
            "nodes_moved": nodes_moved,
            "wallets_reassigned": wallets_reassigned
        }
    
    def _rebalance_shards(self, nodes: List) -> Dict[str, any]:
        """Rebalance load across existing shards - optimized"""
        # Skip expensive rebalancing in fast mode
        if self.fast_mode:
            return {"action": "rebalance_skipped", "nodes_moved": 0}
        
        moves = 0
        
        # Limit rebalancing iterations for speed
        for _ in range(3):  # Reduced from 10 to 3 iterations
            overloaded = None
            underloaded = None
            
            # Use cached load calculations
            for shard_id, metrics in self.shard_metrics.items():
                if len(metrics.load_history) >= 3:
                    avg_load = sum(metrics.load_history) / len(metrics.load_history)
                    if avg_load > self.load_threshold_high:
                        overloaded = shard_id
                    elif avg_load < self.load_threshold_low:
                        underloaded = shard_id
            
            if overloaded is not None and underloaded is not None:
                # Move one node from overloaded to underloaded - simplified
                nodes_in_overloaded = [
                    node for node in nodes
                    if getattr(node, 'shard_id', None) == overloaded
                ]
                
                if nodes_in_overloaded:
                    node_to_move = nodes_in_overloaded[0]  # Take first instead of random
                    node_to_move.shard_id = underloaded
                    self.node_to_shard[node_to_move.id] = underloaded
                    
                    self.shard_metrics[overloaded].node_count -= 1
                    self.shard_metrics[underloaded].node_count += 1
                    moves += 1
            else:
                break
        
        return {
            "action": "rebalance",
            "nodes_moved": moves
        }
    
    def _renumber_shards(self, removed_shard: int, nodes: List) -> None:
        """Renumber shards after removal to maintain consecutive numbering"""
        # Update all references to shards above the removed one
        for node in nodes:
            if hasattr(node, 'shard_id') and node.shard_id > removed_shard:
                node.shard_id -= 1
                self.node_to_shard[node.id] = node.shard_id
        
        for wallet_id, shard_id in self.wallet_to_shard.items():
            if shard_id > removed_shard:
                self.wallet_to_shard[wallet_id] = shard_id - 1
        
        # Renumber metrics dictionary
        new_metrics = {}
        for shard_id, metrics in self.shard_metrics.items():
            if shard_id < removed_shard:
                new_metrics[shard_id] = metrics
            elif shard_id > removed_shard:
                metrics.shard_id = shard_id - 1
                new_metrics[shard_id - 1] = metrics
        
        self.shard_metrics = new_metrics
    
    def get_shard_info(self) -> Dict[str, any]:
        """Get current shard configuration and metrics"""
        info = {
            "shard_count": self.shard_count,
            "shards": {}
        }
        
        for shard_id, metrics in self.shard_metrics.items():
            info["shards"][shard_id] = {
                "node_count": metrics.node_count,
                "avg_load": metrics.get_average_load(),
                "cross_shard_ratio": metrics.get_cross_shard_ratio(),
                "avg_latency": metrics.avg_latency,
                "total_transactions": metrics.transaction_count
            }
        
        return info
    
    def get_performance_summary(self) -> Dict[str, any]:
        """Get overall performance metrics - optimized"""
        if self.fast_mode:
            # Skip expensive calculations in fast mode
            total_tx = sum(metrics.transaction_count for metrics in self.shard_metrics.values())
            return {
                "total_transactions": total_tx,
                "cross_shard_transactions": 0,
                "cross_shard_ratio": 0.0,
                "avg_throughput": total_tx,  # Simplified
                "total_adaptations": self.total_adaptations,
                "current_shards": self.shard_count
            }
        
        # Standard calculations
        total_tx = sum(metrics.transaction_count for metrics in self.shard_metrics.values())
        total_cross_shard = sum(metrics.cross_shard_tx_count for metrics in self.shard_metrics.values())
        
        cross_shard_ratio = total_cross_shard / total_tx if total_tx > 0 else 0
        
        return {
            "total_transactions": total_tx,
            "cross_shard_transactions": total_cross_shard,
            "cross_shard_ratio": cross_shard_ratio,
            "avg_throughput": total_tx,  # Simplified calculation
            "total_adaptations": self.total_adaptations,
            "current_shards": self.shard_count
        }
    
    def print_shard_status(self, block_number: int) -> None:
        """Print current shard status - optimized"""
        print(f"\n=== Dynamic Shard Status (Block {block_number}) ===")
        print(f"Total Shards: {self.shard_count}")
        
        total_load = 0
        total_cross_shard = 0
        total_tx = 0
        
        for shard_id, metrics in self.shard_metrics.items():
            # Use cached load if available, otherwise calculate
            if metrics.load_history:
                load = sum(metrics.load_history) / len(metrics.load_history)
            else:
                load = 0
            
            cross_ratio = metrics.get_cross_shard_ratio()
            
            total_load += load
            total_cross_shard += metrics.cross_shard_tx_count
            total_tx += metrics.transaction_count
            
            status = "OVERLOADED" if load > self.load_threshold_high else \
                     "UNDERLOADED" if load < self.load_threshold_low else "NORMAL"
            
            # Skip latency display since we're not tracking it
            print(f"Shard {shard_id}: {metrics.node_count} nodes, "
                  f"Load: {load:.1f} tx/node, Cross-shard: {cross_ratio:.1%} [{status}]")
        
        if total_tx > 0:
            overall_cross_ratio = total_cross_shard / total_tx
            avg_load = total_load / self.shard_count
            print(f"Overall: Avg Load: {avg_load:.1f}, "
                  f"Cross-shard Ratio: {overall_cross_ratio:.1%}, "
                  f"Total Adaptations: {self.total_adaptations}")
        
        print("=" * 50)

    @property
    def shards(self) -> Dict[int, ShardMetrics]:
        """Property to access shards (for compatibility with coordinator)"""
        return self.shard_metrics
    
    def get_average_load(self) -> float:
        """Calculate average load across all shards"""
        if not self.shard_metrics:
            return 0.0
        total_load = sum(
            len(metrics.tx_history) / max(metrics.node_count, 1) 
            for metrics in self.shard_metrics.values()
        )
        return total_load / len(self.shard_metrics)
    
    def evaluate_and_adapt_shards(self, block_num: int):
        """Check if we need to split/merge shards - keep it simple"""
        # Skip if too soon since last change
        if block_num - self.last_adaptation_block < self.adaptation_cooldown:
            return
            
        # Find busy and quiet shards
        busy_shards = []
        quiet_shards = []
        
        for shard_id, metrics in self.shard_metrics.items():
            avg_load = sum(metrics.load_history) / max(len(metrics.load_history), 1)
            if avg_load > self.load_threshold_high and self.shard_count < self.max_shards:
                busy_shards.append(shard_id)
            elif avg_load < self.load_threshold_low and self.shard_count > self.min_shards:
                quiet_shards.append(shard_id)
        
        # Split a busy shard
        if busy_shards and self.shard_count < self.max_shards:
            self._simple_split(busy_shards[0])
            self.adaptation_count += 1
            self.last_adaptation_block = block_num
            
        # Merge quiet shards  
        elif len(quiet_shards) >= 2 and self.shard_count > self.min_shards:
            self._simple_merge(quiet_shards[0], quiet_shards[1])
            self.adaptation_count += 1 
            self.last_adaptation_block = block_num
    
    def _simple_split(self, shard_id):
        """Split a shard - keep it simple"""
        new_shard_id = self.shard_count
        self.shard_count += 1
        self.shard_metrics[new_shard_id] = ShardMetrics(new_shard_id)
        
        # Move half the nodes to new shard
        nodes_to_move = self.shard_metrics[shard_id].node_count // 2
        self.shard_metrics[shard_id].node_count -= nodes_to_move
        self.shard_metrics[new_shard_id].node_count = nodes_to_move
    
    def _simple_merge(self, shard1, shard2):
        """Merge two shards - keep it simple"""
        if shard1 not in self.shard_metrics or shard2 not in self.shard_metrics:
            return  # Skip if shards don't exist
            
        # Move all nodes from shard2 to shard1
        self.shard_metrics[shard1].node_count += self.shard_metrics[shard2].node_count
        
        # Remove shard2
        del self.shard_metrics[shard2]
        self.shard_count -= 1
        
        # Update wallet assignments from shard2 to shard1
        for wallet_id, current_shard in list(self.wallet_to_shard.items()):
            if current_shard == shard2:
                self.wallet_to_shard[wallet_id] = shard1
