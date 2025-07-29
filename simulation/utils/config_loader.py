import json
import os


def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)


def load_chain_config(chain_name, config_dir):
    chain_file_path = os.path.join(config_dir, 'chains', f'{chain_name}.json')
    
    if not os.path.exists(chain_file_path):
        chains_dir = os.path.join(config_dir, 'chains')
        if os.path.exists(chains_dir):
            available_chains = [f.replace('.json', '') for f in os.listdir(chains_dir) if f.endswith('.json')]
            available_chains_str = ', '.join(available_chains)
        else:
            available_chains_str = "none (chains directory not found)"
        raise ValueError(f"Chain '{chain_name}' not found. Available chains: {available_chains_str}")
    
    return load_config(chain_file_path)


def load_workload_config(workload_name, config_dir):
    workload_file_path = os.path.join(config_dir, 'workloads', f'{workload_name}.json')
    
    if not os.path.exists(workload_file_path):
        workloads_dir = os.path.join(config_dir, 'workloads')
        if os.path.exists(workloads_dir):
            available_workloads = [f.replace('.json', '') for f in os.listdir(workloads_dir) if f.endswith('.json')]
            available_workloads_str = ', '.join(available_workloads)
        else:
            available_workloads_str = "none (workloads directory not found)"
        raise ValueError(f"Workload '{workload_name}' not found. Available workloads: {available_workloads_str}")
    
    return load_config(workload_file_path)


def merge_configs(base_config, chain_config):
    merged = base_config.copy()

    for key, value in chain_config.items():
        if key in ['reward', 'halving', 'blocktime', 'blocksize']:
            merged['simulation'][key] = value
    
    return merged


def apply_workload_config(config, workload_config):
    merged = config.copy()
    
    if 'wallets' in workload_config:
        merged['simulation']['wallets'] = workload_config['wallets']
    if 'transactions_per_wallet' in workload_config:
        merged['simulation']['transactions'] = workload_config['transactions_per_wallet']
    if 'transaction_interval' in workload_config:
        merged['simulation']['interval'] = workload_config['transaction_interval']
    
    return merged
