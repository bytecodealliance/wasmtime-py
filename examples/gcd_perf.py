import wasmtime.loader
import time
from math import gcd as math_gcd
from gcd import gcd_func as wasm_gcd
from gcd_alt import gcd as wasm_gcd_alt

def python_gcd(x, y):
    while y:
        x, y = y, x % y
    return abs(x)

N = 1_000
by_name = locals()
for name in 'math_gcd', 'python_gcd', 'wasm_gcd', 'wasm_gcd_alt':
    gcdf = by_name[name]
    start_time = time.perf_counter()
    for _ in range(N):
        g = gcdf(16516842, 154654684)
    total_time = time.perf_counter() - start_time
    print(total_time, "\t\t", name)
