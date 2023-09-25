# Example of instantiating a wasm module and calling an export on it

from wasmtime import Store, Module, Instance
from functools import partial
store = Store()
module = Module.from_file(store.engine, './examples/gcd.wat')
instance = Instance(store, module, [])
gcd = instance.exports(store)["gcd"]
gcd_func = partial(gcd, store)
gcd_func_val = partial(gcd._call_val, store)
print("gcd(6, 27) = %d" % gcd(store, 6, 27))
print("gcd(6, 27) = %d" % gcd_func(6, 27))
print("gcd(6, 27) = %d" % gcd_func_val(6, 27))
