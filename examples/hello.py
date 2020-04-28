from wasmtime import Store, Module, Instance, Func, FuncType

# Almost all operations in wasmtime require a contextual "store" argument to be
# shared amongst objects
store = Store()

# Here we can compile a `Module` which is then ready for instantiation
# afterwards
module = Module.from_file(store, './examples/hello.wat')

# Our module needs one import, so we'll create that here.


def say_hello():
    print("Hello from Python!")


hello = Func(store, FuncType([], []), say_hello)

# And with all that we can instantiate our module and call the export!
instance = Instance(module, [hello])
instance.exports["run"]()
