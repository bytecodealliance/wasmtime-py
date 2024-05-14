from pathlib import Path


def test_bare_funcs(bindgen_testcase):
    store, root = bindgen_testcase(
        guest_code_dir=Path(__file__).parent,
        world_name='barefuncs',
    )
    assert root.foo(store, 10) == 11
