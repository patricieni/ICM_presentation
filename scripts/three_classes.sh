
python run_random_forest.py -d imputed_dataset_no_censoring_26022018_MICE.csv -l 1.2years 4years more -v 400 1200 -lr 0.03 -o scores_3mice.jpg cfm3_mice.jpg

python run_random_forest.py -d imputed_dataset_no_censoring_26022018_Amelia1.csv -l 1.2years 4years more -v 400 1200 -lr 0.03 -o scores_3amelia.jpg cfm_3amelia.jpg

python run_random_forest.py -d imputed_dataset_no_censoring_26022018_kNN.csv -l 1.2years 4years more -v 400 1200 -lr 0.03 -o scores_3knn.jpg cfm_3knn.jpg
