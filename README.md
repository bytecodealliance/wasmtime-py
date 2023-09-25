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

The package currently supports 64-bit builds of Python 3.8+ on x86\_64 Windows,
macOS, and Linux, as well as on arm64 macOS and Linux.

## Versioning

`wasmtime-py` follows the Wasmtime versioning scheme, with a new major version being
released every month. As with Wasmtime itself, new major versions of `wasmtime-py`
can contain changes that break code written against the previous major version.

Since every installed Python package needs to agree on a single version of
`wasmtime-py`, to use the upper bound on the major version in the dependency
requirement should be bumped reguarly, ideally as soon as a new `wasmtime-py`
version is released. To automate this process it is possible to use
the [whitequark/track-pypi-dependency-version][] script. [YoWASP/runtime][] is
an example of a project that automatically publishes releases on PyPI once a new
version of `wasmtime-py` is released if it passes the testsuite.

[whitequark/track-pypi-dependency-version]: https://github.com/whitequark/track-pypi-dependency-version
[YoWASP/runtime]: https://github.com/YoWASP/runtime

## Usage

In this example, we compile and instantiate a WebAssembly module and use it from Python:

```python
from wasmtime import Store, Module, Instance, Func, FuncType

store = Store()
module = Module(store.engine, """
  (module
    (func $hello (import "" "hello"))
    (func (export "run") (call $hello))
  )
""")

def say_hello():
    print("Hello from Python!")
hello = Func(store, FuncType([], []), say_hello)

instance = Instance(store, module, [hello])
run = instance.exports(store)["run"]
run(store)
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

## Components

The `wasmtime` package has initial support for running WebAssembly components in
Python with high-level bindings. WebAssembly components are defined by the
[component model] and are a flagship feature under development for Wasmtime and
its bindings. Components enable communication between the host and WebAssembly
guests with richer types than the numerical primitives supported by core
WebAssembly. For example with a component Python can pass a string to wasm and
back.

Components are represented as `*.wasm` binaries in the same manner as core
WebAssembly modules. With a component binary you can generate Python bindings
with:

```sh
$ python -m wasmtime.bindgen the-component.wasm --out-dir the-bindings
```

An example of using this can be done with the [`wasm-tools`] repository. For
example with this core wasm module at `demo.wat`:

```wasm
(module
  (import "python" "print" (func $print (param i32 i32)))
  (memory (export "memory") 1)

  (func (export "run")
    i32.const 100   ;; base pointer of string
    i32.const 13    ;; length of string
    call $print)

  (data (i32.const 100) "Hello, world!")
)
```

and with this [`*.wit`] interface at `demo.wit`:

```text
package my:demo

world demo {
  import python: interface {
    print: func(s: string)
  }

  export run: func()
}
```

And this `demo.py` script

```python
from demo import Root, RootImports, imports
from wasmtime import Store

class Host(imports.Python):
    def print(self, s: str):
        print(s)

def main():
    store = Store()
    demo = Root(store, RootImports(Host()))
    demo.run(store)

if __name__ == '__main__':
    main()
```

```sh
$ wasm-tools component embed demo.wit demo.wat -o demo.wasm
$ wasm-tools component new demo.wasm -o demo.component.wasm
$ python -m wasmtime.bindgen demo.component.wasm --out-dir demo
$ python demo.py
Hello, world!
```

The generated package `demo` has all of the requisite exports/imports into the
component bound. The `demo` package is additionally annotated with types to
assist with type-checking and self-documentation as much as possible.

[component model]: https://github.com/WebAssembly/component-model
[`wasm-tools`]: https://github.com/bytecodealliance/wasm-tools
[`*.wit`]: https://github.com/WebAssembly/component-model/blob/main/design/mvp/WIT.md

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).
