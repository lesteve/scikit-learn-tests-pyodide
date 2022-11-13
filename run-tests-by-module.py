import subprocess
import shlex
import sys
import fcntl
import os
import time
import itertools
import unittest

# This is the output of the command run from the scikit-learn root folder:
# find sklearn -name tests | sort | perl -pe 's@/tests@@' | perl -pe 's@/@.@g'
test_submodules_str = """
sklearn.cluster
sklearn.compose
sklearn.covariance
sklearn.cross_decomposition
sklearn.datasets
sklearn.decomposition
sklearn.ensemble._hist_gradient_boosting
sklearn.ensemble
sklearn.experimental
sklearn.feature_extraction
sklearn.feature_selection
sklearn.gaussian_process
sklearn.impute
sklearn.inspection._plot
sklearn.inspection
sklearn.linear_model._glm
sklearn.linear_model
sklearn._loss
sklearn.manifold
sklearn.metrics.cluster
sklearn.metrics._plot
sklearn.metrics
sklearn.mixture
sklearn.model_selection
sklearn.neighbors
sklearn.neural_network
sklearn.preprocessing
sklearn.semi_supervised
sklearn.svm
sklearn
sklearn.tree
sklearn.utils
"""

test_submodules = test_submodules_str.split()

expected_test_results_by_category = {
    "failed": [
        "sklearn.experimental",
        "sklearn.feature_extraction",
        "sklearn._loss",
        "sklearn.svm",
        "sklearn.tree",
    ],
    "fatal error or timeout": [
        "sklearn.decomposition",
        "sklearn.ensemble",
        "sklearn.feature_selection",
        "sklearn.inspection",
        "sklearn.linear_model",
        "sklearn",
        "sklearn.utils",
    ],
    "passed": [
        "sklearn.cluster",
        "sklearn.compose",
        "sklearn.covariance",
        "sklearn.cross_decomposition",
        "sklearn.datasets",
        "sklearn.ensemble._hist_gradient_boosting",
        "sklearn.gaussian_process",
        "sklearn.impute",
        "sklearn.inspection._plot",
        "sklearn.linear_model._glm",
        "sklearn.manifold",
        "sklearn.metrics.cluster",
        "sklearn.metrics._plot",
        "sklearn.metrics",
        "sklearn.mixture",
        "sklearn.model_selection",
        "sklearn.neighbors",
        "sklearn.neural_network",
        "sklearn.preprocessing",
        "sklearn.semi_supervised",
    ],
}


def set_non_blocking(file_):
    """Needed to ensure that .read do not block if there is nothing to be read"""
    fd = file_.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def execute_command_with_timeout(command_list, timeout_without_output):
    """Run command while showing its stdout and stderr continuously.

    Returns
    -------
    dict containing exit_code, stdout, stderr
    """
    last_time_with_output = time.time()
    p = subprocess.Popen(
        command_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    set_non_blocking(p.stdout)
    set_non_blocking(p.stderr)

    stdout_list = []
    stderr_list = []
    exit_code = None

    while exit_code is None:
        exit_code = p.poll()
        if exit_code is None:
            this_stdout = p.stdout.readline()
            this_stderr = p.stderr.readline()
        else:
            # process has finished, need to read all the remaining output
            this_stdout = p.stdout.read()
            this_stderr = p.stderr.read()

        if this_stdout:
            last_time_with_output = time.time()
            print(this_stdout, end="")
            stdout_list.append(this_stdout)
        if this_stderr:
            last_time_with_output = time.time()
            sys.stderr.write(this_stderr)
            stderr_list.append(this_stderr)

        command_timed_out = (
            time.time() - last_time_with_output
        ) > timeout_without_output
        if command_timed_out:
            p.kill()

        if exit_code is not None or command_timed_out:
            stdout = "".join(stdout_list)
            stderr = "".join(stderr_list)

            sys.stdout.flush()
            sys.stderr.flush()

            return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}

        time.sleep(0.01)


def run_tests_for_module(module_str):
    timeout_without_output = 60
    command_str = f"node --experimental-fetch scikit-learn-pytest.js -v {module_str}"
    command_list = shlex.split(command_str)
    command_result = execute_command_with_timeout(
        command_list=command_list, timeout_without_output=timeout_without_output
    )

    if command_result["exit_code"] is None:
        print(f"{module_str} timed out", flush=True)
    else:
        print(f"{module_str} exited with exit code {command_result['exit_code']}", flush=True)

    return command_result


def exit_code_to_category(exit_code):
    if exit_code == 0:
        return "passed"
    if exit_code == 1:
        return "failed"
    if exit_code == 2:
        return "tests collection error"
    if exit_code == 4:
        return "pytest usage error"
    if exit_code == 5:
        return "no test collected"

    # this also covers exit code 3 which is pytest internal error, because this
    # is one of the symptom of a wasm memory corruption
    return "fatal error or timeout"


def print_summary(module_results):
    print()
    print("=" * 80)
    print("Test results summary")
    print("=" * 80)

    for each in module_results:
        print(f"{each['module']} {each['category']} (exit code {each['exit_code']})")

    print()
    print("-" * 80)
    print("Grouped by category:")
    print("-" * 80)

    def fun(each):
        return each["category"]

    test_results_by_category = {
        category: [each["module"] for each in group]
        for category, group in itertools.groupby(sorted(module_results, key=fun), fun)
    }
    for category, module_list in test_results_by_category.items():
        print(f"category {category} ({len(module_list)} modules)")
        for each in module_list:
            print(f"    {each}")

    # Compare test results with expectations. Easiest way I found to compare
    # dicts with a good error message is to use unittest
    tc = unittest.TestCase()
    # to show full info about the diff
    tc.maxDiff = None
    test_results_with_sets = {k: set(v) for k, v in test_results_by_category.items()}
    expected_test_results_with_sets = {
        k: set(v) for k, v in expected_test_results_by_category.items()
    }
    tc.assertDictEqual(expected_test_results_with_sets, test_results_with_sets)


def main():
    module_results = []

    custom_pytest_args = " ".join(sys.argv[1:])
    if custom_pytest_args:
        global test_submodules
        test_submodules = [" ".join(sys.argv[1:])]

    for module in test_submodules:
        print("-" * 80, flush=True)
        print(module, flush=True)
        print("-" * 80, flush=True)
        this_module_result = run_tests_for_module(module)
        this_module_result["module"] = module
        this_module_result["category"] = exit_code_to_category(
            this_module_result["exit_code"]
        )
        module_results.append(this_module_result)

    # When using custom pytest args, we run a single pytest command and it does
    # not make sense to compare results to expectation
    if not custom_pytest_args:
        print_summary(module_results)


if __name__ == "__main__":
    main()
