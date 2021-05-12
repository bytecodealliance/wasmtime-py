# Example of instantiating two modules which link to each other.

from wasmtime import Engine, Store, Module, Linker, WasiConfig

engine = Engine()

# Load and compile our two modules
linking1 = Module.from_file(engine, "examples/linking1.wat")
linking2 = Module.from_file(engine, "examples/linking2.wat")

# Set up our linker which is going to be linking modules together. We
# want our linker to have wasi available, so we set that up here as well.
linker = Linker(engine)
linker.define_wasi()

# Create a `Store` to hold instances, and configure wasi state
store = Store(engine)
wasi = WasiConfig()
wasi.inherit_stdout()
store.set_wasi(wasi)

# Instantiate our first module which only uses WASI, then register that
# instance with the linker since the next linking will use it.
linking2 = linker.instantiate(store, linking2)
linker.define_instance(store, "linking2", linking2)

# And with that we can perform the final link and the execute the module.
linking1 = linker.instantiate(store, linking1)
run = linking1.exports(store)["run"]
run(store)
