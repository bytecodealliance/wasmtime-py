"""Test suite for testing generated code with guest code written in Python.

These tests work by allowing you to write a WIT file, implement the guest
code in Python via componentize-py, and then test the generated Python
bindings. To add a new test, first create the needed fixtures:

* Create a new sub directory.
* Within that directory create a `.wit` file.
* Create an `app.py` file in that directory implementing the guest code.

Then to write the test itself:

* Define the params of the testcase with `BindgenTestCase`.
* Generate the Python bindings using `generate_bindings()`.  This will also
  build the `app.wasm` file using `componentize-py`.
* `generate_bindings()` returns the store and the instantiated `Root` object
  which you can then test.


## Example

Given this directory:

```
bare_funcs/
├── app.py          <-- guest code implementation
├── barefuncs       <-- componentize-py bindings
│   ├── __init__.py
│   └── types.py
└── component.wit   <-- test .wit file
```

With a `component.wit` file of:

```wit
package component:barefuncs;

world barefuncs {
  export foo: func(a: s32) -> s32;
}
```

And guest code of:

```python
class Barefuncs:
    def foo(self, a: int) -> int:
        return a + 1
```

You can write a testcase for this using:

```python
def test_bare_funcs():
    testcase = BindgenTestCase(
        guest_code_dir='bare_funcs',
        world_name='barefuncs',
    )
    store, root = generate_bindings(testcase)
    assert root.foo(store, 10) == 11
```

"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from wasmtime.bindgen import generate
import wasmtime
import contextlib
import importlib
import tempfile
import subprocess
import shutil


TEST_ROOT = Path(__file__).parent
BINDGEN_DIR = TEST_ROOT / 'generated'


@contextlib.contextmanager
def chdir(dirname: Path):
    original = os.getcwd()
    try:
        os.chdir(str(dirname))
        yield
    finally:
        os.chdir(original)


@dataclass
class BindgenTestCase:
    world_name: str
    guest_code_dir: str
    app_dir: Path = field(init=False)
    wit_filename: str = 'component.wit'
    app_name: str = 'app'

    def __post_init__(self):
        self.app_dir = TEST_ROOT / self.guest_code_dir

    @property
    def wit_full_path(self):
        return self.app_dir.joinpath(self.wit_filename)

    @property
    def testsuite_name(self):
        # The name of the directory that contains the
        # guest Python code is used as the identifier for
        # package names, etc.
        return self.app_dir.name


def generate_bindings(testcase: BindgenTestCase):
    wit_path = testcase.wit_full_path
    componentize_py = shutil.which('componentize-py')
    if componentize_py is None:
        raise RuntimeError("Could not find componentize-py executable.")
    with tempfile.NamedTemporaryFile('w') as f:
        output_wasm = str(f.name + '.wasm')
        with chdir(testcase.app_dir):
            subprocess.run([
                componentize_py, '-d', str(wit_path), '-w', testcase.world_name,
                'componentize', '--stub-wasi', testcase.app_name,
                '-o', output_wasm
            ], check=True)
            # Once we've done that now generate the python bindings.
            testsuite_name = testcase.testsuite_name
            with open(output_wasm, 'rb') as out:
                # Mapping of filename -> content_bytes
                results = generate(testsuite_name, out.read())
            for filename, contents in results.items():
                path = BINDGEN_DIR / testsuite_name / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)
    # Return an instantiated module for the caller to test.
    pkg = importlib.import_module(f'.generated.{testsuite_name}',
                                  package=__package__)
    store = wasmtime.Store()
    root = pkg.Root(store)
    return store, root
