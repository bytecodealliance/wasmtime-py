import sys
import pytest

# componentize-py requires Python 3.10
if sys.version_info < (3, 10):
    pytest.skip("skipping componentize-py tests", allow_module_level=True)
