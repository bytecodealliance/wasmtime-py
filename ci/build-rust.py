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


def main():
    print('======================= Building bindgen.wasm =====================')

    subprocess.run(
        ['cargo', 'build', '--release', '--target=wasm32-wasi', '-p=bindgen'],
        cwd='rust'
    ).check_returncode()

    core = 'rust/target/wasm32-wasi/release/bindgen.wasm'
    wasi = 'ci/wasi_preview1_component_adapter.wasm'
    component = 'rust/target/component.wasm'

    print('======================= Building component.wasm ===================')

    subprocess.run(
        ['wasm-tools', 'component', 'new', core, '--adapt', f'wasi_snapshot_preview1={wasi}', '-o', component],
    ).check_returncode()

    print('======================= Bootstrapping with native platform ========')

    subprocess.run(
        ['cargo', 'run', '-p=bindgen', '--features=cli', 'target/component.wasm', '../wasmtime/bindgen/generated'],
        cwd='rust'
    ).check_returncode()


if __name__ == '__main__':
    main()
