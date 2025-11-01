# This example shows how you can use the `wasmtime.loader` module to load wasm
# components without having to generate bindings manually

import wasmtime, wasmtime.loader

def run():
    import loader_component_add  # type: ignore

    store = wasmtime.Store()
    component = loader_component_add.Root(store)
    assert component.add(store, 1, 2) == 3

if __name__ == '__main__':
    run()
