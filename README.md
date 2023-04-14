# Description

Proof of concept repo to run the scikit-learn tests in Pyodide.

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

# Building from sources

On Linux, install the expected version of Python and pyodide-build
```
conda create -n pyodide python=3.10.2
conda activate pyodide
pip install pyodide-build==0.22.0a3
```
and the matching version of [Emscripten toolchain](https://emscripten.org/docs/getting_started/downloads.html),
```
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install 3.1.24
./emsdk 3.1.24
source ./emsdk_env.sh
```
Then you can build a Emscripten/wasm wheel with,
```
cd scikit-learn/
pyodide build
```

# Manually curated list of issues

## Test failures

### Failures that need investigation:
- plenty of errors in `sklearn._loss.tests.test_loss::test_loss_dtype` some memmap issues

### Tests to be skipped or xfailed

Should be skipped because tests use a subprocess:
- `sklearn.experimental.tests.test_enable_hist_gradient_boosting.py::test_import_raises_warning`
- `sklearn.experimental.tests.test_enable_iterative_imputer.py::test_imports_strategies`
- `sklearn.experimental.tests.test_enable_successive_halving.py::test_imports_strategies`

Should be skipped (or xfailed) because lack of feature in wasm, see
https://github.com/numpy/numpy/pull/21895#issuecomment-1311525881
- `sklearn.feature_extraction.tests.test_text.py::test_tfidf_no_smoothing`
