import shlex
import sys
import itertools
import unittest
import asyncio

# This is the output of the command run from the scikit-learn root folder:
# find sklearn -name tests | sort | perl -pe 's@/@.@g'
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

expected_test_results = {
    "sklearn.cluster.tests": ["passed"],
    "sklearn.compose.tests": ["passed"],
    "sklearn.covariance.tests": ["passed"],
    "sklearn.cross_decomposition.tests": ["passed"],
    "sklearn.datasets.tests": ["passed"],
    "sklearn.decomposition.tests": ["passed"],
    "sklearn.ensemble._hist_gradient_boosting.tests": ["passed"],
    "sklearn.ensemble.tests": ["fatal error or timeout"],
    "sklearn.experimental.tests": ["failed"],
    "sklearn.feature_extraction.tests": ["failed"],
    "sklearn.feature_selection.tests": ["fatal error or timeout", "failed"],
    "sklearn.gaussian_process.tests": ["passed"],
    "sklearn.impute.tests": ["passed"],
    "sklearn.inspection._plot.tests": ["passed"],
    "sklearn.inspection.tests": ["fatal error or timeout"],
    "sklearn.linear_model._glm.tests": ["passed"],
    "sklearn.linear_model.tests": ["fatal error or timeout"],
    "sklearn._loss.tests": ["failed"],
    "sklearn.manifold.tests": ["passed"],
    "sklearn.metrics.cluster.tests": ["passed"],
    "sklearn.metrics._plot.tests": ["passed"],
    "sklearn.metrics.tests": ["passed"],
    "sklearn.mixture.tests": ["passed"],
    "sklearn.model_selection.tests": ["passed"],
    "sklearn.neighbors.tests": ["passed"],
    "sklearn.neural_network.tests": ["passed"],
    "sklearn.preprocessing.tests": ["passed"],
    "sklearn.semi_supervised.tests": ["passed"],
    "sklearn.svm.tests": ["failed"],
    "sklearn.tests": ["failed", "fatal error or timeout"],
    "sklearn.tree.tests": ["failed"],
    "sklearn.utils.tests": ["failed"],
}


async def _read_stream(stream, cb, timeout_without_output):
    while True:
        loop = asyncio.get_event_loop_policy().get_event_loop()

        async def readline(stream):
            return await stream.readline()

        task = loop.create_task(readline(stream))

        line = await asyncio.wait_for(task, timeout_without_output)
        line = line.decode()
        if line:
            cb(line)
        else:
            break


async def _stream_subprocess(cmd, stdout_cb, stderr_cb, timeout_without_output):
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    loop = asyncio.get_event_loop_policy().get_event_loop()

    stdout_task = loop.create_task(
        _read_stream(
            process.stdout, stdout_cb, timeout_without_output=timeout_without_output
        )
    )
    stderr_task = loop.create_task(
        _read_stream(
            process.stderr, stderr_cb, timeout_without_output=timeout_without_output
        )
    )

    stdout_result, stderr_result = await asyncio.gather(
        stdout_task, stderr_task, return_exceptions=True
    )

    if isinstance(stdout_result, asyncio.exceptions.TimeoutError) and isinstance(
        stderr_result, asyncio.exceptions.TimeoutError
    ):
        process.kill()
        # return None for timeout
        return

    return await process.wait()


def execute_command_with_timeout(command_list, timeout_without_output):
    """Run command while showing its stdout and stderr continuously.

    Returns
    -------
    dict containing exit_code, stdout, stderr
    """
    loop = asyncio.get_event_loop_policy().get_event_loop()

    stdout_list = []
    stderr_list = []

    def stdout_cb(line):
        print(line, end="")
        stdout_list.append(line)

    def stderr_cb(line):
        sys.stderr.write(line)
        stderr_list.append(line)

    rc = loop.run_until_complete(
        _stream_subprocess(command_list, stdout_cb, stderr_cb, timeout_without_output)
    )
    stdout = "\n".join(stdout_list)
    stderr = "\n".join(stderr_list)
    return {"exit_code": rc, "stdout": stdout, "stderr": stderr}


def run_tests_for_module(module_str):
    timeout_without_output = 60
    command_str = f"node --experimental-fetch scikit-learn-pytest.js --pyargs {module_str} -v --durations 10"
    command_list = shlex.split(command_str)
    command_result = execute_command_with_timeout(
        command_list=command_list, timeout_without_output=timeout_without_output
    )

    if command_result["exit_code"] is None:
        print(f"{module_str} timed out", flush=True)
    else:
        print(
            f"{module_str} exited with exit code {command_result['exit_code']}",
            flush=True,
        )

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
        expected_categories = expected_test_results[each["module"]]
        print(
            f"{each['module']} {each['category']} (exit code {each['exit_code']}), "
            f"expected {expected_categories}"
        )

    print()
    print("-" * 80)
    print("Grouped by category")
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

    sys.stdout.flush()

    mismatches = []
    for each in module_results:
        expected_categories = expected_test_results[each["module"]]
        if each["category"] not in expected_categories:
            message = (
                f"{each['module']} result expected in {expected_categories}, "
                f"got {each['category']!r} instead"
            )
            mismatches.append(message)

    if mismatches:
        print('mismatch')
        mismatches_str = "\n".join(mismatches)
        print("-" * 80)
        print("Unexpected test results")
        print("-" * 80)
        print(mismatches_str)
        return 1

    print("Test results matched expected ones")
    return 0


def main():
    module_results = []

    custom_pytest_args = shlex.join(sys.argv[1:])
    if custom_pytest_args:
        global test_submodules
        test_submodules = [custom_pytest_args]

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
        exit_code = print_summary(module_results)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
