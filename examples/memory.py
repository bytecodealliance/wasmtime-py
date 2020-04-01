# An example of how to interact with wasm memory.
#
# Here a small wasm module is used to show how memory is initialized, how to
# read and write memory through the `Memory` object, and how wasm functions
# can trap when dealing with out-of-bounds addresses.

from wasmtime import Store, Module, Instance, Trap, MemoryType, Memory, Limits

# Create our `Store` context and then compile a module and create an
# instance from the compiled module all in one go.
wasmtime_store = Store()
module = Module.from_file(wasmtime_store, "examples/memory.wat")
instance = Instance(module, [])

# Load up our exports from the instance
memory = instance.get_export("memory").memory()
size = instance.get_export("size").func()
load = instance.get_export("load").func()
store = instance.get_export("store").func()

print("Checking memory...")
assert(memory.size() == 2)
assert(memory.data_len() == 0x20000)

# Note that usage of `data_ptr` is unsafe! This is a raw C pointer which is not
# bounds checked at all. We checked our `data_len` above but you'll want to be
# very careful when accessing data through `data_ptr()`
assert(memory.data_ptr()[0] == 0)
assert(memory.data_ptr()[0x1000] == 1)
assert(memory.data_ptr()[0x1003] == 4)

assert(size.call() == 2)
assert(load.call(0) == 0)
assert(load.call(0x1000) == 1)
assert(load.call(0x1003) == 4)
assert(load.call(0x1ffff) == 0)


def assert_traps(func):
    try:
        func()
        assert(False)
    except Trap:
        pass


# out of bounds trap
assert_traps(lambda: load.call(0x20000))

print("Mutating memory...")
memory.data_ptr()[0x1003] = 5
store.call(0x1002, 6)
# out of bounds trap
assert_traps(lambda: store.call(0x20000, 0))

assert(memory.data_ptr()[0x1002] == 6)
assert(memory.data_ptr()[0x1003] == 5)
assert(load.call(0x1002) == 6)
assert(load.call(0x1003) == 5)

# Grow memory.
print("Growing memory...")
assert(memory.grow(1))
assert(memory.size() == 3)
assert(memory.data_len() == 0x30000)

assert(load.call(0x20000) == 0)
store.call(0x20000, 0)
assert_traps(lambda: load.call(0x30000))
assert_traps(lambda: store.call(0x30000, 0))

# Memory can fail to grow
assert(not memory.grow(1))
assert(memory.grow(0))

print("Creating stand-alone memory...")
memorytype = MemoryType(Limits(5, 5))
memory2 = Memory(wasmtime_store, memorytype)
assert(memory2.size() == 5)
assert(not memory2.grow(1))
assert(memory2.grow(0))
