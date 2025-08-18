import json
import os

def load_json(name):
    # First try the chain-specific directory
    chain_path = os.path.join("config", "chains", f"{name}.json")
    if os.path.exists(chain_path):
        with open(chain_path) as f:
            return json.load(f)
    
    # Fallback to workload directory
    workload_path = os.path.join("config", "workloads", f"{name}.json")
    if os.path.exists(workload_path):
        with open(workload_path) as f:
            return json.load(f)
    
    # Last fallback to old path for compatibility
    old_path = os.path.join("configs", f"{name}.json")
    with open(old_path) as f:
        return json.load(f)

def get_defaults(args):
    # Valid simulation parameter names
    valid_params = {
        'nodes', 'neighbors', 'miners', 'hashrate', 'blocktime', 'reward', 
        'wallets', 'transactions', 'interval', 'blocksize', 'blocks', 
        'print', 'debug', 'halving', 'init_reward', 'blocks_limit', 
        'print_int', 'halving_interval'
    }
    
    merged = {}
    if args.chain:
        chain_config = load_json(args.chain)
        # Chain configs are flat, not wrapped in "simulation"
        if "simulation" in chain_config:
            config_data = chain_config["simulation"]
        else:
            # For flat chain configs, use the config directly but filter
            config_data = chain_config
        
        # Only include valid simulation parameters
        for k, v in config_data.items():
            if k in valid_params:
                merged[k] = v
                
    if args.workload:
        workload_config = load_json(args.workload)
        # Workload configs might have "simulation" wrapper
        if "simulation" in workload_config:
            config_data = workload_config["simulation"]
        else:
            config_data = workload_config
            
        # Only include valid simulation parameters
        for k, v in config_data.items():
            if k in valid_params:
                merged[k] = v
                
    return {k: v for k, v in merged.items() if getattr(args, k, None) is None}
