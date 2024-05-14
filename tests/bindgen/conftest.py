"""Fixtures to define test suites for generated code Python guest code.

These tests work by allowing you to write a WIT file, implement the guest
code in Python via componentize-py, and then test the generated Python
bindings. To add a new test, first create the needed fixtures:

* Create a new sub directory.
* Within that directory create a `.wit` file.
* Create an `app.py` file in that directory implementing the guest code.

Then to write the test itself:

* Create a `test_<name>.py` in the same directory.
* Use the `bindgest_testcase` in your test to create the wasm component
  and generate python bindings for this component.

## Example

Given this directory:

```
bare_funcs/
├── app.py          <-- guest code implementation
├── barefuncs       <-- componentize-py bindings
│   ├── __init__.py
│   └── types.py
├── component.wit   <-- test .wit file
└── test_mycomp.py  <-- pytest test case of bindings
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
from pathlib import Path


def test_bare_funcs(bindgen_testcase):
    testcase = bindgen_testcase(
        guest_code_dir=Path(__file__).parent,
        world_name='barefuncs',
    )
    store, root = generate_bindings(testcase)
    assert root.foo(store, 10) == 11
```

"""
from pathlib import Path
from dataclasses import dataclass, field
import importlib
import tempfile
import subprocess
import shutil

from pytest import fixture

import wasmtime
from wasmtime.bindgen import generate


TEST_ROOT = Path(__file__).parent
BINDGEN_DIR = TEST_ROOT / 'generated'


@dataclass
class BindgenTestCase:
    guest_code_dir: Path
    world_name: str
    wit_filename: str = 'component.wit'
    app_dir: Path = field(init=False)
    app_name: str = field(init=False, default='app', repr=False)

    def __post_init__(self):
        self.app_dir = Path(self.guest_code_dir).resolve()

    @property
    def wit_full_path(self):
        return self.guest_code_dir.joinpath(self.wit_filename)

    @property
    def testsuite_name(self):
        # The name of the directory that contains the
        # guest Python code is used as the identifier for
        # package names, etc.
        return self.guest_code_dir.name


def generate_bindings(guest_code_dir: Path,
                      world_name: str,
                      wit_filename: str = 'component.wit'):
    tc = BindgenTestCase(
            guest_code_dir=guest_code_dir,
            world_name=world_name,
            wit_filename=wit_filename)
    return _generate_bindings(tc)


def _generate_bindings(testcase: BindgenTestCase):
    wit_path = testcase.wit_full_path
    componentize_py = shutil.which('componentize-py')
    if componentize_py is None:
        raise RuntimeError("Could not find componentize-py executable.")
    with tempfile.NamedTemporaryFile('w') as f:
        output_wasm = str(f.name + '.wasm')
        subprocess.run([
            componentize_py, '-d', str(wit_path), '-w', testcase.world_name,
            'componentize', '--stub-wasi', testcase.app_name,
            '-o', output_wasm
        ], check=True, cwd=testcase.guest_code_dir)
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


@fixture
def bindgen_testcase():
    return generate_bindings
