import time
from sortedcontainers import SortedList

# Globals
network_data = io_requests = total_tx = total_coins = 0
pool = []
HEADER_SIZE = 1024
YEAR = 365 * 24 * 3600
start_time = time.time()
pool = SortedList(key=lambda x: -x[0])
