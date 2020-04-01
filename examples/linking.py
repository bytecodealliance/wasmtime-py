# Example of instantiating two modules which link to each other.

from wasmtime import Store, Module, Linker, WasiConfig, WasiInstance

store = Store()

# First set up our linker which is going to be linking modules together. We
# want our linker to have wasi available, so we set that up here as well.
linker = Linker(store)
wasi = WasiInstance(store, "wasi_snapshot_preview1", WasiConfig())
linker.define_wasi(wasi)

# Load and compile our two modules
linking1 = Module.from_file(store, "examples/linking1.wat")
linking2 = Module.from_file(store, "examples/linking2.wat")

# Instantiate our first module which only uses WASI, then register that
# instance with the linker since the next linking will use it.
linking2 = linker.instantiate(linking2)
linker.define_instance("linking2", linking2)

# And with that we can perform the final link and the execute the module.
linking1 = linker.instantiate(linking1)
run = linking1.get_export("run").func()
run.call()
