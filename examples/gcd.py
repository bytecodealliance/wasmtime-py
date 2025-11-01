# Example of instantiating a wasm module and calling an export on it

from wasmtime import Store, Module, Instance

def run():
    store = Store()
    module = Module.from_file(store.engine, './examples/gcd.wat')
    instance = Instance(store, module, [])
    gcd = instance.exports(store)["gcd"]

    print("gcd(6, 27) = %d" % gcd(store, 6, 27))

if __name__ == '__main__':
    run()
