<div align="center">
  <h1><code>wasmtime-py</code></h1>

  <p>
    <strong>Python embedding of
    <a href="https://github.com/bytecodealliance/wasmtime">Wasmtime</a></strong>
  </p>

  <strong>A <a href="https://bytecodealliance.org/">Bytecode Alliance</a> project</strong>

  <p>
    <a href="https://github.com/alexcrichton/wasmtime-py/actions?query=workflow%3ACI">
      <img src="https://github.com/alexcrichton/wasmtime-py/workflows/CI/badge.svg" alt="CI status"/>
    </a>
    <a href="https://pypi.org/project/wasmtime/">
      <img src="https://img.shields.io/pypi/v/wasmtime.svg" alt="Latest Version"/>
    </a>
    <a href="https://pypi.org/project/wasmtime/">
      <img src="https://img.shields.io/pypi/pyversions/wasmtime.svg" alt="Latest Version"/>
    </a>
    <a href="https://alexcrichton.github.io/wasmtime-py/">
      <img src="https://img.shields.io/badge/docs-master-green" alt="Documentation"/>
    </a>
    <a href="https://alexcrichton.github.io/wasmtime-py/coverage/">
      <img src="https://img.shields.io/badge/coverage-master-green" alt="Code Coverage"/>
    </a>
  </p>

</div>

## Installation

You can install this extension via:

```
pip install wasmtime
```

Currently only x86\_64 Windows, macOS, and Linux are supported for this Python
extension.

## Usage

An example of compiling a module and importing functionality from Python can be
done with:

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

instance = Instance(module, [hello])
instance.get_export("run").func().call()
```

Be sure to check out the [`examples` directory] which has other usage patterns
as well as the [full API documentation][apidoc]

[`examples` directory]: https://github.com/alexcrichton/wasmtime-py/tree/master/examples
[apidoc]: https://alexcrichton.github.io/wasmtime-py/

If your wasm modules works this way, then you can also import the wasm module
directly into Python without instantiating it yourself:

```python
# Import the custom loader for `*.wasm` files
import wasmtime.loader

# Assuming `your_wasm_file.wasm` is in the python load path...
import your_wasm_file

# And now you're instantiated and ready to go!
print(your_wasm_file.run())
```

## Contributing

So far this extension has been written by folks who are primarily Rust
programmers, so it's highly likely that there's some faux pas in terms of Python
idioms. Feel free to send a PR to help make things more idiomatic if you see
something!

To work on this extension locally you'll first want to clone the project:

```sh
$ git clone https://github.com/alexcrichton/wasmtime-py
$ cd wasmtime-py
```

Next up you'll acquire a Wasmtime installation. This extension expects your
platform's shared library to exist at `wasmtime/wasmtime.pyd`. You can download
the latest development version of Wasmtime with `python download-wasmtime.py`
(this is what CI does). Otherwise if you have a local checkout of Wasmtime you
can symlink its `libwasmtime.so` (or equivalent) to `wasmtime/wasmtime.pyd`.

After you've got Wasmtime set up you can make sure it works by running all the
tests:

```sh
$ pip install pytest
$ pytest
```

And after that you should be good to go!

### CI and Releases

It's intended that this module is a largely automated process for all of the
particulars. The CI for this project does a few different things:

* API docs are generated for pushes to the master branch and are [rendered
  online][apidoc]
* Test coverage information is generated for pushes to the master branch and are
  [available online](https://alexcrichton.github.io/wasmtime-py/coverage/)
* Each push to `master` will publish a release to
  [test.pypi.org](https://test.pypi.org/project/wasmtime/) for local inspection.
* Tagged commits will automatically be published to
  [pypi.org](https://pypi.org/project/wasmtime/)

Otherwise all commits/PRs run the full test suite and also check for style with
`flake8`
