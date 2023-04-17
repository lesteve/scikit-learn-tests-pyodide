# Description

This repository runs the scikit-learn tests in Pyodide using the scikit-learn
development version and the Pyodide development version.

As of mid-April 2023, the full scikit-learn test suite passes :tada:. There are a few
xfailed tests due to Pyodide limitations related to threads, processes,
floating point exceptions and memmaps, see [conftest.py](./conftest.py) for
more details.

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

