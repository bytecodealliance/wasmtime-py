from . import BindgenTestCase, generate_bindings

def test_bare_funcs():
    testcase = BindgenTestCase(
        guest_code_dir='bare_funcs',
        world_name='barefuncs',
    )
    store, root = generate_bindings(testcase)
    assert root.foo(store, 10) == 11


# This test works, but needs wasmtime-py#232 merged to pass.
#
# def test_export_resources():
#     testcase = BindgenTestCase(
#         guest_code_dir='export_resources',
#         world_name='testworld',
#     )
#     store, root = generate_bindings(testcase)
#     interface = root.my_interface_name()
#     instance = interface.DemoResourceClass(store, 'myname')
#     result = instance.greet(store, 'Hello there')
#     assert result == 'Hello there, myname!'


def test_lists():
    testcase = BindgenTestCase(
        guest_code_dir='list_types',
        world_name='lists'
    )
    store, root = generate_bindings(testcase)
    assert root.strings(store, '') == ''
    assert root.strings(store, 'a') == 'a'
    assert root.strings(store, 'hello world') == 'hello world'
    assert root.strings(store, 'hello ⚑ world') == 'hello ⚑ world'

    assert root.bytes(store, b'') == b''
    assert root.bytes(store, b'a') == b'a'
    assert root.bytes(store, b'\x01\x02') == b'\x01\x02'

    assert root.ints(store, []) == []
    assert root.ints(store, [1]) == [1]
    assert root.ints(store, [1, 2, 100, 10000]) == [1, 2, 100, 10000]

    assert root.string_list(store, []) == []
    assert root.string_list(store, ['']) == ['']
    assert root.string_list(
        store, ['a', 'b', '', 'd', 'hello']
    ) == ['a', 'b', '', 'd', 'hello']
