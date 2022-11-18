# The `codegen` directory here is intended to test the bindings generator for
# components in Python. Each file represents a distinct test where an input
# wasm file is bound and then the generated bindings are imported dynamically.
#
# This structure is done so a general `pytest` will execute everything,
# generating bindings during test collection and otherwise setting up everything
# to be naturally checked with mypy and other tests configured.

from wasmtime import wat2wasm
from wasmtime.bindgen import generate
from pathlib import Path
import os


# Helper function to generate bindings for the `wat` specified into the
# `generated` sub-folder. After calling this method the bindings can be
# imported with:
#
#   from .generated.name import Name
#
# and then used to type-check everything.
def bindgen(name: str, wat: str) -> None:
    files = generate(name, wat2wasm(wat))
    root = Path(__file__).parent.joinpath('generated')
    dst = root.joinpath(name)
    for name, contents in files.items():
        # If the file already has the desired contents then skip writing. This
        # is an attempt to fix CI issues on windows.
        file = dst.joinpath(name)
        if file.exists():
            with open(file, 'rb') as f:
                if f.read() == contents:
                    continue

        # Write the contents to a temporary file and then attempt to atomically
        # replace the previous file, if any, with the new contents. This
        # is done to hopefully fix an apparent issue in `pytest` where it seems
        # that there are multiple threads of the python interpreter, perhaps for
        # pytest itself, mypy, and flake8, and overwriting files in-place causes
        # issues are partial files may be seen.
        tmp_file = file.with_suffix('.tmp')
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        tmp_file.write_bytes(contents)
        os.replace(tmp_file, file)


REALLOC = """
    (global $last (mut i32) (i32.const 1000))
    (func $realloc (export "realloc")
        (param $old_ptr i32)
        (param $old_size i32)
        (param $align i32)
        (param $new_size i32)
        (result i32)

        (local $ret i32)

        ;; Test if the old pointer is non-null
        local.get $old_ptr
        if
            ;; If the old size is bigger than the new size then
            ;; this is a shrink and transparently allow it
            local.get $old_size
            local.get $new_size
            i32.gt_u
            if
                local.get $old_ptr
                return
            end

            ;; otherwise fall through to allocate a new chunk which will later
            ;; copy data over
        end

        ;; align up `$last`
        (global.set $last
            (i32.and
                (i32.add
                    (global.get $last)
                    (i32.add
                        (local.get $align)
                        (i32.const -1)))
                (i32.xor
                    (i32.add
                        (local.get $align)
                        (i32.const -1))
                    (i32.const -1))))

        ;; save the current value of `$last` as the return value
        global.get $last
        local.set $ret

        ;; bump our pointer
        (global.set $last
            (i32.add
                (global.get $last)
                (local.get $new_size)))

        ;; while `memory.size` is less than `$last`, grow memory
        ;; by one page
        (loop $loop
            (if
                (i32.lt_u
                    (i32.mul (memory.size) (i32.const 65536))
                    (global.get $last))
                (then
                    i32.const 1
                    memory.grow
                    ;; test to make sure growth succeeded
                    i32.const -1
                    i32.eq
                    if unreachable end

                    br $loop)))


        ;; ensure anything necessary is set to valid data by spraying a bit
        ;; pattern that is invalid
        local.get $ret
        i32.const 0xde
        local.get $new_size
        memory.fill

        ;; If the old pointer is present then that means this was a reallocation
        ;; of an existing chunk which means the existing data must be copied.
        local.get $old_ptr
        if
            local.get $ret          ;; destination
            local.get $old_ptr      ;; source
            local.get $old_size     ;; size
            memory.copy
        end

        local.get $ret
    )
"""
