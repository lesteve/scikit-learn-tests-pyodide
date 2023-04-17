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

tests_to_mark = [
    # sklearn/experimental/tests
    (
        "test_enable_hist_gradient_boosting.py::test_import_raises_warning",
        xfail,
        process_msg,
    ),
    (
        "test_enable_iterative_imputer.py::test_imports_strategies",
        xfail,
        process_msg,
    ),
    (
        "test_enable_successive_halving.py::test_imports_strategies",
        xfail,
        process_msg,
    ),
    # sklearn/feature_extraction/tests
    ("test_text.py::test_tfidf_no_smoothing", xfail, fp_exception_msg),
    # sklearn/_loss/tests
    ("test_loss.py::test_loss_dtype.+True", xfail, memmap_msg),
    (
        "test_testing.py::test_create_memmap_backed_data.+True",
        xfail,
        memmap_msg,
    ),
    # sklearn/tests
    (
        "test_common.py::test_import_all_consistency",
        xfail,
        importlib_msg,
    ),
    ("test_config.py::test_config_threadsafe$", xfail, "no threading support"),
    (
        "test_discriminant_analysis.py::test_qda_regularization",
        xfail,
        fp_exception_msg,
    ),
    ("test_docstring_parameters.py::test_tabs", xfail, importlib_msg),
    # sklearn/utils/tests
    (
        "test_testing.py::test_create_memmap_backed_data.+True",
        xfail,
        memmap_msg,
    ),
    (
        "test_testing.py::test_memmap_on_contiguous_data",
        xfail,
        memmap_msg,
    ),
    (
        "test_readonly_wrapper.py::test_readonly_array_wrapper.+"
        "_create_memmap_backed_data",
        xfail,
        memmap_msg,
    ),
]


def pytest_collection_modifyitems(config, items):
    for item in items:
        path, line, name = item.reportinfo()
        path = str(path)
        full_name = f"{path}::{name}"
        for pattern, mark, reason in tests_to_mark:
            if re.search(pattern, full_name):
                item.add_marker(mark(reason=reason))
