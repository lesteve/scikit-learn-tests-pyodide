import re
import pytest

xfail = pytest.mark.xfail

fp_exception_msg = (
    "no floating point exceptions, "
    "see https://github.com/numpy/numpy/pull/21895#issuecomment-1311525881"
)
process_msg = "no process support"
thread_msg = "no thread support"
memmap_msg = "memmap not fully supported"
importlib_msg = "importlib not supported for Pyodide packages"

# No tests to xfail/skip since this is done inside scikit-learn since we run
# the test suite inside Pyodide, See
# https://github.com/scikit-learn/scikit-learn/pull/27346 for more details.
tests_to_mark = [
]


def pytest_collection_modifyitems(config, items):
    for item in items:
        path, line, name = item.reportinfo()
        path = str(path)
        full_name = f"{path}::{name}"
        for pattern, mark, reason in tests_to_mark:
            if re.search(pattern, full_name):
                item.add_marker(mark(reason=reason))
