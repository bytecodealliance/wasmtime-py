# Helper script to download a precompiled binary of the wasmtime dll for the
# current platform. Currently always downloads the dev release of wasmtime.

import io
import os
import platform
import shutil
import sys
import tarfile
import urllib.request
import zipfile


def main(platform, arch):
    is_zip = False
    if arch == 'AMD64':
        arch = 'x86_64'
    if platform == 'linux':
        filename = 'wasmtime-dev-{}-linux-c-api.tar.xz'.format(arch)
        libname = '_libwasmtime.so'
    elif platform == 'win32':
        filename = 'wasmtime-dev-{}-windows-c-api.zip'.format(arch)
        is_zip = True
        libname = '_wasmtime.dll'
    elif platform == 'darwin':
        filename = 'wasmtime-dev-{}-macos-c-api.tar.xz'.format(arch)
        libname = '_libwasmtime.dylib'
    else:
        raise RuntimeError("unknown platform: " + sys.platform)

    url = 'https://github.com/bytecodealliance/wasmtime/releases/download/dev/'
    url += filename
    print('Download', url)
    dirname = '{}-{}'.format(platform, arch)
    dst = os.path.join('wasmtime', dirname, libname)
    try:
        shutil.rmtree(os.path.dirname(dst))
    except Exception:
        pass
    os.makedirs(os.path.dirname(dst))

    with urllib.request.urlopen(url) as f:
        contents = f.read()

    if is_zip:
        t = zipfile.ZipFile(io.BytesIO(contents))
        for member in t.namelist():
            if not member.endswith('.dll'):
                continue
            contents = t.read(member)
            with open(dst, "wb") as f:
                f.write(contents)
            sys.exit(0)
    else:
        t = tarfile.open(fileobj=io.BytesIO(contents))
        for member in t.getmembers():
            linux_so = member.name.endswith('.so')
            macos_dylib = member.name.endswith('.dylib')
            if not linux_so and not macos_dylib:
                continue
            contents = t.extractfile(member).read()
            with open(dst, "wb") as f:
                f.write(contents)
            sys.exit(0)

    raise RuntimeError("failed to find dynamic library")


if __name__ == '__main__':
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        main(sys.platform, platform.machine())
