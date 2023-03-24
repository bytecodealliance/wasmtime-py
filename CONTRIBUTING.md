# Contributing to `wasmtime-py`

`wasmtime-py` is a [Bytecode Alliance] project. It follows the Bytecode
Alliance's [Code of Conduct] and [Organizational Code of Conduct].

So far this extension has been written by folks who are primarily Rust
programmers, so feel free to create a PR to help make things more idiomatic if
you see something!

## Set Up

You'll need to acquire a [Wasmtime] installation. The `wasmtime-py` package
expects your platform's shared library to exist at `wasmtime/{host}/_{library}`.
You can download the latest development version of Wasmtime by running a script
in the top-level directory of the package's source (this is what CI does):

[wasmtime]: https://wasmtime.dev/

```sh
$ python ci/download-wasmtime.py
```

Otherwise if you have a local checkout of Wasmtime you can symlink its
`libwasmtime.so` (or equivalent) to `wasmtime/linux-x86_64/_libwasmtime.so` (or
equivalent).

Next the bindings generation requires compiling some Rust code to WebAssembly,
which can be done with:

```sh
$ python ci/build-rust.py
```

Finally, install the dev dependencies with `pip`:

```
$ pip install -e ".[testing]"
```

## Testing

After you've completed the set up steps, you can run the tests locally with
`pytest`:

```
$ pytest
```

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
and other errors using [ruff](https://beta.ruff.rs/docs/).

[Bytecode Alliance]: https://bytecodealliance.org/
[Code of Conduct]: https://github.com/bytecodealliance/wasmtime/blob/main/CODE_OF_CONDUCT.md
[Organizational Code of Conduct]: https://github.com/bytecodealliance/wasmtime/blob/main/ORG_CODE_OF_CONDUCT.md
[Wasmtime]: https://github.com/bytecodealliance/wasmtime
[apidoc]: https://bytecodealliance.github.io/wasmtime-py/
