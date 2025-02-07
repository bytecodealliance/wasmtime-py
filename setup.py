# type: ignore

import setuptools
import os
import subprocess

with open("README.md", "r") as fh:
    long_description = fh.read()

version = "29.0.0"

# Give unique version numbers to all commits so our publication-on-each commit
# works on main
if 'PROD' not in os.environ:
    res = subprocess.run(['git', 'rev-list', 'HEAD', '--count'], capture_output=True, encoding="utf8")
    version += '.dev' + res.stdout.strip()

setuptools.setup(
    name="wasmtime",
    version=version,
    author="The Wasmtime Project Developers",
    author_email="hello@bytecodealliance.org",
    description="A WebAssembly runtime powered by Wasmtime",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache-2.0 WITH LLVM-exception",
    url="https://github.com/bytecodealliance/wasmtime-py",
    project_urls={
        "Bug Tracker": "https://github.com/bytecodealliance/wasmtime-py/issues",
        "Documentation": "https://bytecodealliance.github.io/wasmtime-py/",
        "Source Code": "https://github.com/bytecodealliance/wasmtime-py",
    },
    packages=['wasmtime'],
    install_requires=['importlib_resources>=5.10'],
    include_package_data=True,
    package_data={"wasmtime": ["py.typed"]},
    python_requires='>=3.9',
    test_suite="tests",
    extras_require={
        'testing': [
            'coverage',
            'pytest',
            'pycparser',
            'pytest-mypy',
            "componentize-py;platform_system!='Windows' or platform_machine=='x86_64'",
        ],
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Interpreters',
        'Programming Language :: Rust',
    ]
)
