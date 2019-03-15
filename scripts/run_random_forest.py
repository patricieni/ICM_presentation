import os
from pathlib import Path
import argparse
from datetime import timedelta

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn import tree
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, accuracy_score, confusion_matrix, r2_score
from sklearn.metrics import log_loss, auc, classification_report, roc_auc_score, roc_curve
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler, label_binarize
from sklearn.ensemble import AdaBoostClassifier, ExtraTreesClassifier, BaggingClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV


import sys
sys.path.append("../code")
from ICM_utils import helper, evaluation, metrics


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


data_path = str(Path(os.getcwd()).parent) + "/data/"
results_path = str(Path(os.getcwd()).parent) + "/results/random_forests/"

# Args Parser
parser = argparse.ArgumentParser(description='Random forests script')

# Not sure for labels if I have to say str
parser.add_argument('-d', '--dataset', nargs="?", type=str,
                    help='Path for dataset to use (csv)', required=True)
parser.add_argument('-l', '--labels', nargs="+", type=str,
                    help='The exact labels required for splitting the expectancy variable, i.e. 1.5years 4years, more for 3 categories', required=True)
parser.add_argument('-v', '--values', nargs="+", type=int,
                    help='Values where to split the dataset (in days, i.e. 500 ~ 1.5 years )', required=True)
parser.add_argument('-lr', '--learning_rate', nargs="?",
                    type=float, help='Learning rate for rf', required=True)
parser.add_argument('-g', '--gbm', nargs='?', type=str2bool,
                    help='Should we take only gbm patients ?', required=False, default='no')
parser.add_argument('-o', '--output', nargs="+", type=str,
                    help='Output files', required=False)

args = parser.parse_args()
dataset = args.dataset
labels = args.labels
cut_points = args.values
learning_rate = args.learning_rate
output = args.output
gbm_only = args.gbm

# Clean up from the imputation
df = pd.read_csv(data_path+dataset)
df.drop("Unnamed: 0", axis=1, inplace=True)

if gbm_only:
    print("Using only GBM patients for predictions")
    df = df[df.Tumor_type == "GBM"]

# Try with three classes first
df.loc[:, "life_expectancy_bin"] = helper.binning(
    df.life_expectancy, cut_points, labels)
# print(pd.value_counts(df_amelia.life_expectancy_bin, sort=False))
print(df.life_expectancy_bin.values)
print("\n")
# Print the data in the output
for column in df:
    unique_vals = np.unique(df[column])
    nr_vals = len(unique_vals)
    if nr_vals < 20:
        print('Number of values for attribute {}: {} -- {}'.format(column,
                                                                   nr_vals, unique_vals))
    else:
        print('Number of values for attribute {}: {}'.format(column, nr_vals))
print("\n")

non_dummy_cols = ['Tumor_grade', 'IDH_TERT', 'life_expectancy',
                  'life_expectancy_bin', 'Gender', 'IK', 'Age_surgery', 'TERT']
dummy_cols = list(set(df.columns) - set(non_dummy_cols))

df = pd.get_dummies(df, columns=dummy_cols)

df.Gender.replace(to_replace={'M': 1, 'F': 0}, inplace=True)
df.TERT.replace(to_replace={'wt': 0, 'mutant': 1}, inplace=True)

X = df.drop(["life_expectancy", "life_expectancy_bin"], axis=1)
Y = df.life_expectancy_bin

# Will eventually have multiple runs with stdev
log_losses = []
accuracies = []
random_states = [1332, 1, 5, 8, 100]

for r_state in random_states:
    print("Using random state {0}".format(r_state))
    X_train, X_test, Y_train, Y_test = train_test_split(
        X, Y, test_size=0.20, random_state=r_state)

    # Grid search over a smaller space for estimators
    # Create a model with 400 estimators for the grid search
    rfc = RandomForestClassifier(random_state=1233)

    # Create the parameter grid based on the results of random search
    param_grid = {
        'bootstrap': [True, False],
        'max_depth': [80, 90, 100, 110],
        'max_features': [2, 3],
        'min_samples_leaf': [3, 4, 5],
        'min_samples_split': [8, 10, 12],
        "criterion": ["gini", "entropy"],
        "n_estimators": [20, 30, 400, 1000]
    }

    # Instantiate GRID SEARCH over the space of parameters defined
    # Should we play with CV?
    grid_search = GridSearchCV(estimator=rfc, param_grid=param_grid,
                               n_jobs=-1, verbose=2,  # Do we need jobs and verbose to change?
                               scoring='neg_log_loss', cv=3, return_train_score=True)

    # Fit the model - should not show processing
    grid_search.fit(X_train, Y_train)

    # Random forests n_estimators based on Grid Search
    best_grid = grid_search.best_estimator_
    # grid_accuracy = evaluate(best_grid, test_features, test_labels) - what is this one? what are the test_features?

    l = np.array(labels)
    # Does the below work?
    rfc = best_grid

    rfc.fit(X_train, Y_train)

    # Accuracy on test
    accuracy = rfc.score(X_test, Y_test)

    # XEntropy Error
    probas = rfc.predict_proba(X_test)
    y_pred = np.argmax(probas, axis=1)
    error = log_loss(Y_test, probas)

    accuracies.append(accuracy)
    log_losses.append(error)

print("\n")
if not os.path.isdir(results_path):
    os.mkdir(results_path)

# Should put the below in some sort of plot
print("Saved Results for RF")
print("For {0} class problem --- Score: {1} and Logloss: {2}".format(len(labels),
                                                                     str(accuracies), str(log_losses)))
