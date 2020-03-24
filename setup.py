import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wasmtime",
    version="0.1.0",
    author="The Wasmtime Project Developers",
    author_email="hello@bytecodealliance.org",
    description="A WebAssembly runtime",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bytecodealliance/wasmtime-py",
    packages=setuptools.find_packages(),
    python_requires='>=2.7',
)
