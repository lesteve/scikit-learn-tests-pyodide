import subprocess
import shlex
import sys
import fcntl
import os
import time
import itertools
import unittest

# This is the output of the command run from the scikit-learn root folder:
# find sklearn -name tests | sort | perl -pe 's@\./@@g' | perl -pe 's@/@.@g'
test_submodules_str = """
sklearn.cluster.tests
sklearn.compose.tests
sklearn.covariance.tests
sklearn.cross_decomposition.tests
sklearn.datasets.tests
sklearn.decomposition.tests
sklearn.ensemble._hist_gradient_boosting.tests
sklearn.ensemble.tests
sklearn.experimental.tests
sklearn.feature_extraction.tests
sklearn.feature_selection.tests
sklearn.gaussian_process.tests
sklearn.impute.tests
sklearn.inspection._plot.tests
sklearn.inspection.tests
sklearn.linear_model._glm.tests
sklearn.linear_model.tests
sklearn._loss.tests
sklearn.manifold.tests
sklearn.metrics.cluster.tests
sklearn.metrics._plot.tests
sklearn.metrics.tests
sklearn.mixture.tests
sklearn.model_selection.tests
sklearn.neighbors.tests
sklearn.neural_network.tests
sklearn.preprocessing.tests
sklearn.semi_supervised.tests
sklearn.svm.tests
sklearn.tests
sklearn.tree.tests
sklearn.utils.tests
"""

test_submodules = test_submodules_str.split()

expected_test_results_by_category = {
    "failed": [
        "sklearn.experimental.tests",
        "sklearn.feature_extraction.tests",
        "sklearn._loss.tests",
        "sklearn.svm.tests",
        "sklearn.tree.tests",
    ],
    "fatal error or timeout": [
        "sklearn.decomposition.tests",
        "sklearn.ensemble.tests",
        "sklearn.feature_selection.tests",
        "sklearn.inspection.tests",
        "sklearn.linear_model.tests",
        "sklearn.tests",
        "sklearn.utils.tests",
    ],
    "passed": [
        "sklearn.cluster.tests",
        "sklearn.compose.tests",
        "sklearn.covariance.tests",
        "sklearn.cross_decomposition.tests",
        "sklearn.datasets.tests",
        "sklearn.ensemble._hist_gradient_boosting.tests",
        "sklearn.gaussian_process.tests",
        "sklearn.impute.tests",
        "sklearn.inspection._plot.tests",
        "sklearn.linear_model._glm.tests",
        "sklearn.manifold.tests",
        "sklearn.metrics.cluster.tests",
        "sklearn.metrics._plot.tests",
        "sklearn.metrics.tests",
        "sklearn.mixture.tests",
        "sklearn.model_selection.tests",
        "sklearn.neighbors.tests",
        "sklearn.neural_network.tests",
        "sklearn.preprocessing.tests",
        "sklearn.semi_supervised.tests",
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

            return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}


def run_tests_for_module(module_str):
    timeout_without_output = 60
    command_str = f"node --experimental-fetch scikit-learn-pytest.js {module_str} -v"
    command_list = shlex.split(command_str)
    command_result = execute_command_with_timeout(
        command_list=command_list, timeout_without_output=timeout_without_output
    )

    if command_result["exit_code"] is None:
        print(f"{module_str} timed out")
    else:
        print(f"{module_str} exited with exit code: {command_result['exit_code']}")

    return command_result


def exit_code_to_category(exit_code):
    if exit_code == 0:
        return "passed"
    if exit_code == 1:
        return "failed"
    # this also covers exit code 3 which is pytest internal error
    return "fatal error or timeout"


def print_summary(module_results):
    print()
    print("=" * 80)
    print("Test results summary")
    print("=" * 80)

    for each in module_results:
        print(f"{each['module']} {each['category']} (exit code {each['exit_code']})")

    print()
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
    for module in test_submodules:
        print("-" * 80)
        print(f"testing module {module}")
        print("-" * 80)
        this_module_result = run_tests_for_module(module)
        this_module_result["module"] = module
        this_module_result["category"] = exit_code_to_category(
            this_module_result["exit_code"]
        )
        module_results.append(this_module_result)

    print_summary(module_results)


if __name__ == "__main__":
    main()
