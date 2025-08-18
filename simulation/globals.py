import time

# Globals
network_data = io_requests = total_tx = total_coins = 0
pool = []
HEADER_SIZE = 1024
YEAR = 365 * 24 * 3600
RADIUS = 6378 # earth radius in km
start_time = time.time()

# Danksharding globals
danksharding_enabled = False
total_blobs_processed = 0
total_blob_data = 0
parallel_speedup = 1.0
