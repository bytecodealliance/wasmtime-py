<div align="center">
  <h1><code>wasmtime-py</code></h1>

  <p>
    <strong>Python embedding of
    <a href="https://github.com/bytecodealliance/wasmtime">Wasmtime</a></strong>
  </p>

  <strong>A <a href="https://bytecodealliance.org/">Bytecode Alliance</a> project</strong>

  <p>
    <a href="https://github.com/bytecodealliance/wasmtime-py/actions?query=workflow%3ACI">
      <img src="https://github.com/bytecodealliance/wasmtime-py/workflows/CI/badge.svg" alt="CI status"/>
    </a>
    <a href="https://pypi.org/project/wasmtime/">
      <img src="https://img.shields.io/pypi/v/wasmtime.svg" alt="Latest Version"/>
    </a>
    <a href="https://pypi.org/project/wasmtime/">
      <img src="https://img.shields.io/pypi/pyversions/wasmtime.svg" alt="Latest Version"/>
    </a>
    <a href="https://bytecodealliance.github.io/wasmtime-py/">
      <img src="https://img.shields.io/badge/docs-main-green" alt="Documentation"/>
    </a>
    <a href="https://bytecodealliance.github.io/wasmtime-py/coverage/">
      <img src="https://img.shields.io/badge/coverage-main-green" alt="Code Coverage"/>
    </a>
  </p>

</div>

## Installation

To install `wasmtime-py`, run this command in your terminal:

```bash
$ pip install wasmtime
```

The package currently supports 64-bit builds of Python 3.6+ on x86\_64 Windows,
macOS, and Linux

## Usage

In this example, we compile and instantiate a WebAssembly module and use it from Python:

```python
from wasmtime import Store, Module, Instance, Func, FuncType

store = Store()
module = Module(store, """
  (module
    (func $hello (import "" "hello"))
    (func (export "run") (call $hello))
  )
""")

def say_hello():
    print("Hello from Python!")
hello = Func(store, FuncType([], []), say_hello)

instance = Instance(store, module, [hello])
run = instance.exports["run"]
run()
```

Be sure to check out the [`examples` directory], which has other usage patterns
as well as the [full API documentation][apidoc] of the `wasmtime-py` package.

[`examples` directory]: https://github.com/bytecodealliance/wasmtime-py/tree/main/examples
[apidoc]: https://bytecodealliance.github.io/wasmtime-py/

If your WebAssembly module works this way, then you can also import the WebAssembly module
directly into Python without explicitly compiling and instantiating it yourself:

```python
# Import the custom loader for `*.wasm` files
import wasmtime.loader

# Assuming `your_wasm_file.wasm` is in the python load path...
import your_wasm_file

# Now you're compiled and instantiated and ready to go!
print(your_wasm_file.run())
```

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).
