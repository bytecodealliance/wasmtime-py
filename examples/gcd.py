# Example of instantiating a wasm module and calling an export on it

from wasmtime import Store, Module, Instance

store = Store()
module = Module.from_file(store.engine, './examples/gcd.wat')
instance = Instance(store, module, [])
gcd = instance.exports["gcd"]

print("gcd(6, 27) = %d" % gcd(6, 27))
