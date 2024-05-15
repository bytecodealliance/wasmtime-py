from pathlib import Path


def test_lists(bindgen_testcase):
    store, root = bindgen_testcase(
        guest_code_dir=Path(__file__).parent,
        world_name='lists',
    )
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
