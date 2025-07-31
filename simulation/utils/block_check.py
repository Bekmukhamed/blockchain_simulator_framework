def calculate_expected_blocks(total_tx, block_size):
    if total_tx <= 0 or block_size <= 0:
        return 0
    return (total_tx + block_size - 1) // block_size


def validate_blocks_count(total_tx, block_size, actual_blocks=None):
    expected = calculate_expected_blocks(total_tx, block_size)
    if actual_blocks is not None and expected != actual_blocks:
        print(f"Expected {expected} blocks, got {actual_blocks}")
    return expected