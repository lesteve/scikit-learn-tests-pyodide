import subprocess
import shlex
import sys
import fcntl
import os
import time
import collections

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
command_result_type = collections.namedtuple("CommandResult", "exit_code stdout stderr")


def set_non_blocking(file_):
    """Needed to ensure that .read do not block if there is nothing to be read"""
    fd = file_.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def execute_command_with_timeout(command_list, timeout):
    """Run command while showing its stdout and stderr continuously.

    Returns
    -------
    command_result_type(exit_code, stdout, stderr)
    """
    start = time.time()
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
            print(this_stdout, end="")
            stdout_list.append(this_stdout)
        if this_stderr:
            sys.stderr.write(this_stderr)
            stderr_list.append(this_stderr)

        command_timed_out = time.time() - start > timeout

        if exit_code is not None or command_timed_out:
            stdout = "".join(stdout_list)
            stderr = "".join(stderr_list)

            return command_result_type(exit_code, stdout, stderr)


def run_tests_for_module(module_str):
    timeout = 5 * 60
    command_str = f"node --experimental-fetch scikit-learn-pytest.js {module_str} -v"
    command_list = shlex.split(command_str)
    command_result = execute_command_with_timeout(
        command_list=command_list, timeout=timeout
    )

    if command_result.exit_code is None:
        print(f"{module_str} timed out")
    else:
        print(f"{module_str} exited with exit code: {command_result.exit_code}")

    return command_result


def print_summary(module_results):
    # TODO: mark some modules which are expected to fail
    # TODO: do better summary at the end to show what happened and exit code base on this

    print()
    print("=" * 80)
    print("Test results summary")
    print("=" * 80)
    for module_str, command_result in module_results.items():
        if command_result.exit_code is None:
            print(f"module {module_str} timed out")
            stdout_last_10_lines = command_result.stdout.splitlines()[-10:]
            print("\n".join(stdout_last_10_lines))
        else:
            print(f"module {module_str} exited with exit code: {command_result.exit_code}")
            stdout_last_10_lines = command_result.stdout.splitlines()[-10:]
            print("\n".join(stdout_last_10_lines))


def main():
    module_results = {}
    for module in test_submodules:
        print("-" * 80)
        print(f"testing module {module}")
        print("-" * 80)
        module_results[module] = run_tests_for_module(module)

    print_summary(module_results)


if __name__ == "__main__":
    main()
