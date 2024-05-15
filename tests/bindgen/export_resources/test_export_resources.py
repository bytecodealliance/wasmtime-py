from pathlib import Path


def test_bare_funcs(bindgen_testcase):
    store, root = bindgen_testcase(
        guest_code_dir=Path(__file__).parent,
        world_name='testworld',
    )
    interface = root.my_interface_name()
    instance = interface.DemoResourceClass(store, 'myname')
    result = instance.greet(store, 'Hello there')
    assert result == 'Hello there, myname!'
