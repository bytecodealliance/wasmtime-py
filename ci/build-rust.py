# This is a script to generate the `wasmtime/bindgen/generated` directory. That
# directory itself exposes the Python-based functionality for generating
# bindings itself, so a bit of a bootstrapping process happens here.
#
# Bindings generation itself is written in Rust since that's where all of the
# `*.wit` tooling is located. That's compiled to a `bindgen.wasm` file and then
# assembled into a `component.wasm` using the `bindgen.wit` world.
#
# From this compiled component we sort of need to run it on itself. To avoid
# that odd bootstrapping problem we work around that by running the bindgen
# on the native platform, on the component, to generate bindings. That
# is then loaded here and re-executed, through wasm, to ensure that everything
# remains the same.

import subprocess
import os
from pathlib import Path


def main():
    print('======================= Building bindgen.wasm =====================')

    subprocess.run(
        ['cargo', 'build', '--release', '--target=wasm32-wasi', '-p=bindgen'],
        cwd='rust'
    ).check_returncode()

    print('======================= Building wasi_snapshot_preview1.wasm ======')

    env = os.environ.copy()
    env['RUSTFLAGS'] = '-Clink-arg=--import-memory -Clink-arg=-zstack-size=0'
    subprocess.run(
        ['cargo', 'build', '--release', '--target', 'wasm32-unknown-unknown', '-p', 'wasi_snapshot_preview1'],
        cwd='rust',
        env=env,
    ).check_returncode()

    core = 'rust/target/wasm32-wasi/release/bindgen.wasm'
    wasi = 'rust/target/wasm32-unknown-unknown/release/wasi_snapshot_preview1.wasm'
    component = 'rust/target/component.wasm'

    print('======================= Building component.wasm ===================')

    subprocess.run(
        ['wasm-tools', 'component', 'new', core, '--adapt', wasi, '-o', component],
    ).check_returncode()

    print('======================= Bootstrapping with native platform ========')

    subprocess.run(
        ['cargo', 'run', '-p=bindgen', '--features=cli', 'target/component.wasm', '../wasmtime/bindgen/generated'],
        cwd='rust'
    ).check_returncode()

    print('======================= Verifying python generates same result ====')

    from wasmtime.bindgen import generate
    with open(component, 'rb') as f:
        wasm = f.read()
    result = generate('bindgen', wasm)
    for name, contents in result.items():
        path = Path('wasmtime/bindgen/generated').joinpath(name)
        with open(path, 'rb') as f:
            contents2 = f.read()
            if contents2 != contents:
                raise RuntimeError('path difference {}' % path)


if __name__ == '__main__':
    main()
