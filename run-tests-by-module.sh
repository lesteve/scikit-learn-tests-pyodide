#!/bin/bash
set -e

mkdir -p logs

function run_tests_for_module {
    # sometimes the command seems to hang, use a timeout of 5 minutes
    timeout -v 300 node --experimental-fetch scikit-learn-pytest.js $1 -v 2>&1 || \
        echo "command timed out" | tee logs/$t.log
}


for t in \
    sklearn._loss.tests \
    sklearn.cluster.tests \
    sklearn.compose.tests \
    sklearn.covariance.tests \
    sklearn.cross_decomposition.tests \
    sklearn.datasets.tests \
    sklearn.decomposition.tests \
    sklearn.ensemble._hist_gradient_boosting.tests \
    sklearn.ensemble.tests \
    sklearn.experimental.tests \
    sklearn.feature_extraction.tests \
    sklearn.feature_selection.tests \
    sklearn.gaussian_process.tests \
    sklearn.impute.tests \
    sklearn.inspection._plot.tests \
    sklearn.inspection.tests \
    sklearn.linear_model._glm.tests \
    sklearn.linear_model.tests \
    sklearn.manifold.tests \
    sklearn.metrics._plot.tests \
    sklearn.metrics.cluster.tests \
    sklearn.metrics.tests \
    sklearn.mixture.tests \
    sklearn.model_selection.tests \
    sklearn.neighbors.tests \
    sklearn.neural_network.tests \
    sklearn.preprocessing.tests \
    sklearn.semi_supervised.tests \
    sklearn.svm.tests \
    sklearn.tests \
    sklearn.tree.tests \
    sklearn.utils.tests
do
    echo '----------------------------------------------------------------------'
    echo tested module: $t
    echo '----------------------------------------------------------------------'
    run_tests_for_module $t
done

