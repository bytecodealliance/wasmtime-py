# This is an example of working with mulit-value modules and dealing with
# multi-value functions.

from wasmtime import Config, Store, Engine, Module, FuncType, Func, ValType, Instance

# Configure our `Store`, but be sure to use a `Config` that enables the
# wasm multi-value feature since it's not stable yet.
print("Initializing...")
config = Config()
config.wasm_multi_value = True
store = Store(Engine(config))

print("Compiling module...")
module = Module.from_file(store, "examples/multi.wat")

print("Creating callback...")
callback_type = FuncType([ValType.i32(), ValType.i64()], [ValType.i64(), ValType.i32()])


def callback(a, b):
    return [b + 1, a + 1]


callback_func = Func(store, callback_type, callback)

print("Instantiating module...")
instance = Instance(module, [callback_func])

print("Extracting export...")
g = instance.exports["g"]

print("Calling export \"g\"...")
results = g(1, 3)
print("> %d %d", results[0], results[1])

assert(results[0] == 4)
assert(results[1] == 2)

print("Calling export \"round_trip_many\"...")
round_trip_many = instance.exports["round_trip_many"]
results = round_trip_many(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

print("Printing result...")
print(">")
for r in results:
    print("  %d" % r)
assert(len(results) == 10)
for i, r in enumerate(results):
    assert(i == r)
