# Description

This repository runs the scikit-learn tests in Pyodide using the scikit-learn
development version and the Pyodide development version.

As of end-September 2023, scikit-learn runs its test suite inside Pyodide
(latest release, which is 0.24.1 at the time of writing) in its CI
:tada::tada::tada:. See `Linux_Nightly_Pyodide` job in
[azure-pipelines.yml](https://github.com/scikit-learn/scikit-learn/blob/main/azure-pipelines.yml),
[script to build Pyodide wheel](https://github.com/scikit-learn/scikit-learn/blob/main/build_tools/azure/install_pyodide.sh)
and [script to test Pyodide wheel](https://github.com/scikit-learn/scikit-learn/blob/main/build_tools/azure/test_script_pyodide.sh).

There are a few xfailed tests due to Pyodide limitations
related to threads, processes, floating point exceptions, memmaps and
importlib. To see the xfailed tests, look at
[this](https://github.com/search?q=repo%3Ascikit-learn%2Fscikit-learn%20_IS_WASM&type=code).

This repository uses artifacts from
https://github.com/lesteve/scipy-tests-pyodide, which builds every day a
Pyodide distribution in debug mode from the Pyodide `main` branch and
scikit-learn from the `main` branch.

# How to run locally

You can run all tests by module like this:
```bash
python run-tests-by-modules.py
```

You can run selected tests with additional pytest arguments like this:
```bash
python run-tests-by-modules.py sklearn.tree -k poisson -q
```

Or do a similar thing it directly with the `js` helper:
```bash
node --experimental-fetch scikit-learn-pytest.js --pyargs sklearn.tree -k poisson -q
```

`scikit-learn-pytest.js` is strongly inspired from a previous version of
https://github.com/numpy/numpy/pull/21895.

