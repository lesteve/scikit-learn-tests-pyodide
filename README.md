# Description

Proof of concept repo to run the scikit-learn tests in Pyodide.

You can run all tests by module like this:
```bash
./run-tests-by-modules.sh
```

You can run selected tests like this:
```bash
node --experimental-fetch scikit-learn-pytest.js --pyargs 'sklearn.tree'
```

`scikit-learn-pytest.js` is strongly inspired from
https://github.com/numpy/numpy/pull/21895.

# Manually curated list of issues

## Test failures

- sklearn.ensemble.tests.test_forest::test_poisson_vs_mse
- sklearn.experimental.tests.test_enable_iterative_imputer.py::test_imports_strategies
- sklearn.experimental.tests.test_enable_successive_halving.py::test_imports_strategies
- sklearn.feature_extraction.tests.test_text.py::test_tfidf_no_smoothing
- plenty of errors in sklearn._loss.tests.test_loss::test_loss_dtype
- sklearn.svm.tests.test_bounds::test_newrand_set_seed[None-81]
- sklearn.tests.test_build::test_openmp_parallelism_enabled
- sklearn.tree.tests.test_tree::test_poisson_vs_mse
- sklearn.utils.tests.test_estimator_checks::test_all_estimators_all_public

## Fatal errors

Two different kind of errors: "null function or function signature mismatch"
and "memory access out of bounds".

- sklearn.decomposition.tests
- sklearn.ensemble.tests
- sklearn.inspection.tests
- sklearn.linear_model.tests
- sklearn.tests
- sklearn.utils.tests

TODO: This would be nice to try to pinpoint whether some particular tests
causes the issue. In my experience the pytest output can not be trusted for
this since it can vary from run to run. `collected-tests.txt` could be used to
run tests by smaller chunks in separate node instances.

