YEAR = 365 * 24 * 3600
network_data = 0
io_requests = 0
pool = []
total_tx = 0
total_coins = 0

def human(n):
    a = abs(n)
    if a >= 1e9: return f'{n/1e9:.1f}B' if n % 1e9 else f'{int(n/1e9)}B'
    if a >= 1e6: return f'{n/1e6:.1f}M' if n % 1e6 else f'{int(n/1e6)}M'
    if a >= 1e3: return f'{n/1e3:.1f}K' if n % 1e3 else f'{int(n/1e3)}K'
    return str(n)
