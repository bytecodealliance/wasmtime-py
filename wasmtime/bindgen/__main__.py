# This is a small utility that developers can use after installing the
# `wasmtime` package by using:
#
#   python3 -m wasmtime.bindgen the-component.wasm --out-dir ./here
#
# This intentionally isn't installed as a global script at this time since I
# don't know of a great name for such a script. Otherwise it's at least
# accessible and usable after a `pip3 install wasmtime`.

from wasmtime.bindgen import generate
from pathlib import Path
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='Wasmtime Bindings Generation',
        description='Generate Python bindings for a component')
    parser.add_argument('filename')
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--name')
    args = parser.parse_args()

    name = Path(args.filename).stem
    if args.name:
        name = args.name

    with open(args.filename, 'rb') as f:
        contents = f.read()
    files = generate(name, contents)
    for name, contents in files.items():
        dst = Path(args.out_dir).joinpath(name)
        if not dst.parent.exists():
            dst.parent.mkdir(parents=True)
        dst.write_bytes(contents)
        print("Generating", dst)


if __name__ == '__main__':
    main()
