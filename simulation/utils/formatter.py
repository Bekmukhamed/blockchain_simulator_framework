# Format large numbers
def human(n):
    a = abs(n)
    if a >= 1e9:
        v, s = n / 1e9, 'B'
    elif a >= 1e6:
        v, s = n / 1e6, 'M'
    elif a >= 1e3:
        v, s = n / 1e3, 'K'
    else:
        return str(int(n))
    return f"{int(v) if v.is_integer() else f'{v:.1f}'}{s}"
