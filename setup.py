import setuptools
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

version = "0.3.0"

# Give unique version numbers to all commits so our publication-on-each commit
# works on master
if 'PROD' not in os.environ:
    stream = os.popen('git rev-list HEAD --count')
    output = stream.read()
    version += '.dev' + output.strip()

setuptools.setup(
    name="wasmtime2",
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
    include_package_data=True,
    python_requires='>=2.7',
    test_suite="tests",
    extras_require={
        'testing': [
            'coverage',
            'pytest',
        ],
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Interpreters',
        'Programming Language :: Rust',
    ]
)
