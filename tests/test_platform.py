import subprocess
import sys


def test_64_bit_check_uses_pointer_size() -> None:
    # A 64-bit interpreter whose sys.maxsize looks 32-bit, as GraalPy's does (#313), must still load wasmtime.
    code = "import sys; sys.maxsize = 2**31 - 1; import wasmtime"
    subprocess.run([sys.executable, "-c", code], check=True)
