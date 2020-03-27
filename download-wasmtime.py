# Helper script to download a precompiled binary of the wasmtime dll for the
# current platform. Currently always downloads the dev release of wasmtime.

import urllib.request
import zipfile
import tarfile
import io
import sys


is_zip = False
if sys.platform == 'linux':
    filename = 'wasmtime-dev-x86_64-linux-c-api.tar.xz'
elif sys.platform == 'win32':
    filename = 'wasmtime-dev-x86_64-windows-c-api.zip'
    is_zip = True
elif sys.platform == 'darwin':
    filename = 'wasmtime-dev-x86_64-macos-c-api.tar.xz'
else:
    raise RuntimeError("unknown platform: " + sys.platform)

url = 'https://github.com/bytecodealliance/wasmtime/releases/download/dev/'
url += filename
print('Download', url)

with urllib.request.urlopen(url) as f:
    contents = f.read()

if is_zip:
    t = zipfile.ZipFile(io.BytesIO(contents))
    for member in t.namelist():
        if not member.endswith('.dll'):
            continue
        contents = t.read(member)
        with open("wasmtime/wasmtime.pyd", "wb") as f:
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
        with open("wasmtime/wasmtime.pyd", "wb") as f:
            f.write(contents)
        sys.exit(0)

raise RuntimeError("failed to find dynamic library")
