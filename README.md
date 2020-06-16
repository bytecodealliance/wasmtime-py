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

To install wasmtime-py, run this command in your terminal:

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

So far this extension has been written by folks who are primarily Rust
programmers, so it's highly likely that there's some faux pas in terms of Python
idioms. Feel free to create a PR to help make things more idiomatic
if you see something!

To work on this extension locally you'll first want to clone the project:

```sh
$ git clone https://github.com/bytecodealliance/wasmtime-py
$ cd wasmtime-py
```

Next up you'll acquire a [Wasmtime] installation. The wasmtime-py package expects
your platform's shared library to exist at `wasmtime/wasmtime.pyd`. You can
download the latest development version of Wasmtime by running a script in the
top-level directory of the package's source (this is what CI does):

[wasmtime]: https://wasmtime.dev/

```sh
$ python download-wasmtime.py
```

Otherwise if you have a local checkout of Wasmtime you can symlink
its `libwasmtime.so` (or equivalent) to `wasmtime/wasmtime.pyd`.

After you've got Wasmtime set up you can check it works by running all the
unit tests:

```sh
$ pip install pytest
$ pytest
```

After that you should be good to go!

### CI and Releases

The CI for this project does a few different things:

* API docs are generated for pushes to the `main` branch and are [published
    online][apidoc].
* Test coverage information is generated for pushes to the `main` branch and are
  [available online](https://bytecodealliance.github.io/wasmtime-py/coverage/).
* Each push to `main` will publish a release to
  [test.pypi.org](https://test.pypi.org/project/wasmtime/) for local inspection.
* Tagged commits will automatically be published to
  [pypi.org](https://pypi.org/project/wasmtime/).

All commits/PRs run the full test suite, and check for code style
and other errors using [flake8](https://flake8.pycqa.org/).
