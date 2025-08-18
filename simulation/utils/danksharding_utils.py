# Danksharding configuration loader
import json
import os
import simulation.globals as sim_globals

def load_danksharding_config():
    """Load Danksharding configuration from config file"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'config', 
        'danksharding.json'
    )
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            danksharding_config = config.get('danksharding', {})
            
            # Set global configuration
            sim_globals.danksharding_enabled = danksharding_config.get('enabled', False)
            
            return danksharding_config
    except FileNotFoundError:
        # Default configuration if file doesn't exist
        return {
            'enabled': False,
            'max_blobs_per_block': 6,
            'max_blob_size': 131072,
            'blob_base_fee': 1,
            'shard_count': 64,
            'blob_inclusion_probability': 0.3
        }

def enable_danksharding():
    """Enable Danksharding for the current simulation"""
    sim_globals.danksharding_enabled = True
    from ..core.blobs import danksharding_config
    danksharding_config.enabled = True
    print("Danksharding enabled for simulation")

def disable_danksharding():
    """Disable Danksharding for the current simulation"""
    sim_globals.danksharding_enabled = False
    from ..core.blobs import danksharding_config
    danksharding_config.enabled = False
    print("Danksharding disabled for simulation")
