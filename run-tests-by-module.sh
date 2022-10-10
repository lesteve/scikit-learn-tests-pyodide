set -e

for t in \
        sklearn.linear_model.tests \
        sklearn.linear_model._glm.tests \
        sklearn.utils.tests \
        sklearn.manifold.tests \
        sklearn.datasets.tests \
        sklearn.metrics.tests \
        sklearn.metrics._plot.tests \
        sklearn.metrics.cluster.tests \
        sklearn.tree.tests \
        sklearn.compose.tests \
        sklearn.experimental.tests \
        sklearn.gaussian_process.tests \
        sklearn.neural_network.tests \
        sklearn.mixture.tests \
        sklearn.impute.tests \
        sklearn.neighbors.tests \
        sklearn.semi_supervised.tests \
        sklearn.ensemble.tests \
        sklearn.ensemble._hist_gradient_boosting.tests \
        sklearn.feature_selection.tests \
        sklearn.model_selection.tests \
        sklearn.covariance.tests \
        sklearn.inspection.tests \
        sklearn.inspection._plot.tests \
        sklearn.decomposition.tests \
        sklearn.cross_decomposition.tests \
        sklearn.svm.tests \
        sklearn.feature_extraction.tests \
        sklearn._loss.tests \
        sklearn.cluster.tests \
        sklearn.preprocessing.tests \
        sklearn.tests
do
    echo tested module: $t
    node --experimental-fetch scikit-learn-pytest.js $t -v 2>&1 | tee logs/$t.log
done

