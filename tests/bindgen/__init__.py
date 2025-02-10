import sys
import pytest
import platform

is_win_arm64 = platform.system() == 'Windows' and platform.machine() == 'ARM64'

# componentize-py requires Python 3.10, and doesn't support Windows on ARM64
if sys.version_info < (3, 10) or is_win_arm64:
    pytest.skip("skipping componentize-py tests", allow_module_level=True)
