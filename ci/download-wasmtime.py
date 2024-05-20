# Helper script to download a precompiled binary of the wasmtime dll for the
# current platform. Currently always downloads the dev release of wasmtime.

import io
import platform
import shutil
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

WASMTIME_VERSION = "v21.0.0"


def main(platform, arch):
    is_zip = False
    version = WASMTIME_VERSION
    if arch == 'AMD64':
        arch = 'x86_64'
    if arch == 'arm64':
        arch = 'aarch64'
    if platform == 'linux':
        filename = 'wasmtime-{}-{}-linux-c-api.tar.xz'.format(version, arch)
        libname = '_libwasmtime.so'
    elif platform == 'win32':
        filename = 'wasmtime-{}-{}-windows-c-api.zip'.format(version, arch)
        is_zip = True
        libname = '_wasmtime.dll'
    elif platform == 'darwin':
        filename = 'wasmtime-{}-{}-macos-c-api.tar.xz'.format(version, arch)
        libname = '_libwasmtime.dylib'
    else:
        raise RuntimeError("unknown platform: " + sys.platform)

    url = 'https://github.com/bytecodealliance/wasmtime/releases/download/{}/'.format(version)
    url += filename
    print('Download', url)
    dirname = '{}-{}'.format(platform, arch)
    dst = Path('wasmtime') / dirname / libname
    try:
        shutil.rmtree(dst.parent)
    except Exception:
        pass
    try:
        shutil.rmtree(Path('wasmtime/include'))
    except Exception:
        pass
    Path(dst).parent.mkdir(parents=True)
    (Path('wasmtime') / 'include/wasmtime').mkdir(parents=True)

    with urllib.request.urlopen(url) as f:
        contents = f.read()

    def final_loc(name):
        parts = name.split('include/')
        print(parts)
        if len(parts) > 1 and name.endswith('.h'):
            return Path('wasmtime') / 'include' / parts[1]
        elif name.endswith('.dll') or name.endswith('.so') or name.endswith('.dylib'):
            if '-min.' in name:
                return None
            return dst
        else:
            return None

    if is_zip:
        t = zipfile.ZipFile(io.BytesIO(contents))
        for member in t.namelist():
            loc = final_loc(member)
            if not loc:
                continue
            contents = t.read(member)
            with open(loc, "wb") as f:
                f.write(contents)
    else:
        t = tarfile.open(fileobj=io.BytesIO(contents))
        for member in t.getmembers():
            loc = final_loc(member.name)
            if not loc:
                continue
            contents = t.extractfile(member).read()
            with open(loc, "wb") as f:
                f.write(contents)

    if not dst.exists():
        raise RuntimeError("failed to find dynamic library")


if __name__ == '__main__':
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        main(sys.platform, platform.machine())
