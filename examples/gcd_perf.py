import time
from math import gcd as math_gcd
from gcd import gcd_func as wasm_gcd, gcd_func_val as wasm_gcd_old


def python_gcd(x, y):
    while y:
        x, y = y, x % y
    return abs(x)


a = 16516842
b = 154654684

print(math_gcd(a, b), python_gcd(a, b), wasm_gcd(a, b), wasm_gcd_old(a, b))

N = 1_000
by_name = locals()
for name in "math_gcd", "python_gcd", "wasm_gcd", "wasm_gcd_old":
    gcdf = by_name[name]
    start_time = time.perf_counter()
    for _ in range(N):
        g = gcdf(a, b)
    total_time = time.perf_counter() - start_time
    print(total_time, "\t\t", name)
