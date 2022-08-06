"""Evaluate the confidence of an ensemble for selecting molecules."""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from tap import Tap


class Args(Tap):
    chemprop_data_path: Path  # Path to CSV file containing ensemble predictions on a test set.
    rf_data_path: Path
    activity_column: str = 'activity'  # Name of the column containing true activity values.
    preds_column_suffix: str = 'preds'  # Suffix of the names of the columns containing predictions.


def evaluate_ensemble_confidence(args: Args) -> None:
    """Evaluate the confidence of an ensemble for selecting molecules."""
    # Load data
    chemprop_data = pd.read_csv(args.chemprop_data_path)
    rf_data = pd.read_csv(args.rf_data_path)

    chemprop_preds_columns = [column for column in chemprop_data.columns if column.endswith(args.preds_column_suffix)]
    rf_preds_columns = [column for column in rf_data.columns if column.endswith(args.preds_column_suffix)]

    chemprop_preds = chemprop_data[chemprop_preds_columns].to_numpy()
    rf_preds = rf_data[rf_preds_columns].to_numpy()

    chemprop_percentiles = chemprop_preds.argsort(axis=0).argsort(axis=0) / (len(chemprop_data) - 1)
    rf_percentiles = rf_preds.argsort(axis=0).argsort(axis=0) / (len(rf_data) - 1)

    model_num = 0

    hit_mask = chemprop_data[args.activity_column] == 1

    # agree = np.abs(chemprop_percentiles[:, model_num] - rf_percentiles[:, model_num]) <= 0.05
    agree = np.abs(chemprop_percentiles[:, model_num] - chemprop_percentiles[:, model_num + 2]) <= 0.05

    print(sum(chemprop_data[args.activity_column] == 1) / len(chemprop_data))
    print(sum(chemprop_data[args.activity_column][agree] == 1) / sum(agree))

    print('Chemprop')
    print(f'ROC-AUC = {roc_auc_score(chemprop_data[args.activity_column][agree], chemprop_percentiles[:, model_num][agree]):.3f}')
    print(f'PRC-AUC = {average_precision_score(chemprop_data[args.activity_column][agree], chemprop_percentiles[:, model_num][agree]):.3f}')
    print()


    print('RF')
    print(f'ROC-AUC = {roc_auc_score(chemprop_data[args.activity_column][agree], rf_percentiles[:, model_num][agree]):.3f}')
    print(f'PRC-AUC = {average_precision_score(chemprop_data[args.activity_column][agree], rf_percentiles[:, model_num][agree]):.3f}')
    print()

    print('Ensemble')
    print(f'ROC-AUC = {roc_auc_score(chemprop_data[args.activity_column][agree], (chemprop_percentiles[:, model_num] + rf_percentiles[:, model_num])[agree]):.3f}')
    print(f'PRC-AUC = {average_precision_score(chemprop_data[args.activity_column][agree], (chemprop_percentiles[:, model_num] + rf_percentiles[:, model_num])[agree]):.3f}')
    print()

    exit()

    import matplotlib.pyplot as plt
    plt.clf()
    # plt.scatter(chemprop_percentiles[:, model_num][~hit_mask], np.abs(chemprop_percentiles[:, model_num] - rf_percentiles[:, model_num])[~hit_mask], label='nonhit', color='blue')
    # plt.scatter(chemprop_percentiles[:, model_num][hit_mask], np.abs(chemprop_percentiles[:, model_num] - rf_percentiles[:, model_num])[hit_mask], label='hit', color='red')
    plt.scatter(chemprop_percentiles[:, model_num][~hit_mask], rf_percentiles[:, model_num][~hit_mask], label='nonhit', color='blue')
    plt.scatter(chemprop_percentiles[:, model_num][hit_mask], rf_percentiles[:, model_num][hit_mask], label='hit', color='red')
    plt.xlabel('Chemprop Percentile')
    # plt.ylabel('Absolute Value Percentile Difference')
    plt.ylabel('RF Percentile')
    plt.legend()
    plt.show()

    exit()


    # Get preds
    preds_columns = [column for column in data.columns if column.endswith(args.preds_column_suffix)]
    all_preds = data[preds_columns].to_numpy()

    # Convert preds scores into percentiles for comparability
    ranking = all_preds.argsort(axis=0).argsort(axis=0)
    all_preds = ranking / (len(data) - 1)  # percentiles

    # Compute variance
    preds_std = np.std(all_preds, axis=1)

    # Use first model's predictions
    pred_column = preds_columns[0]

    # Compute performance of first model as a function of std percentile among ensemble
    # percentiles = np.arange(0, 101, 10)
    percentiles = [0, 90, 95, 100]
    percentile_stds = np.percentile(preds_std, percentiles)

    hit_mask = data[args.activity_column] == 1
    hit_stds = preds_std[hit_mask]
    nonhit_stds = preds_std[~hit_mask]
    print(np.mean(hit_stds))
    print(np.mean(nonhit_stds))
    print()

    preds = all_preds.mean(axis=1)
    print(f'ROC-AUC = {roc_auc_score(data[args.activity_column], preds):.3f}')
    print(f'PRC-AUC = {average_precision_score(data[args.activity_column], preds):.3f}')
    print(f'Positive enrichment = {sum(data[args.activity_column] == 1) / len(data):.3f}')
    print()

    high_score_mask = preds >= 0.98
    # for std in np.arange(0.35, 0.0, -0.05):
    for std in np.arange(0.05, 0.0, -0.005):
        std_mask = preds_std <= std
        mask = high_score_mask & std_mask
        print(f'std = {std:.3f}')
        activities = data[args.activity_column][mask]
        print(activities.value_counts())
        print(f'ROC-AUC = {roc_auc_score(data[args.activity_column][mask], preds[mask]):.3f}')
        print(f'PRC-AUC = {average_precision_score(data[args.activity_column][mask], preds[mask]):.3f}')
        print(f'Positive enrichment = {sum(activities == 1) / len(activities):.3f}')
        print()

    # exit()

    import matplotlib.pyplot as plt
    for model_num in range(len(preds_columns)):
        plt.clf()
        # plt.scatter(all_preds.mean(axis=1), preds_std, color='blue', s=5)
        # plt.scatter(all_preds[:, model_num], preds_std, color='blue', s=5)
        plt.scatter(all_preds.mean(axis=1)[~hit_mask], nonhit_stds, label='nonhit', color='blue', s=5)
        plt.scatter(all_preds.mean(axis=1)[hit_mask], hit_stds, label='hit', color='red', s=5)
        # plt.hist(nonhit_stds, density=True, bins=100, label='nonhit', alpha=0.5)
        # plt.hist(hit_stds, density=True, bins=100, label='hit', alpha=0.5)
        # plt.xlabel('Prediction Score')
        plt.xlabel('Ranking')
        plt.ylabel('Standard Deviation')
        plt.legend()
        plt.show()
        exit()
    exit()

    # for model_num in range(len(preds_columns)):
    #     print(roc_auc_score(data[args.activity_column], all_preds[:, model_num]))
    #     print(average_precision_score(data[args.activity_column], all_preds[:, model_num]))
    #     print()
    #
    # print(roc_auc_score(data[args.activity_column], preds_std))
    # print(average_precision_score(data[args.activity_column], preds_std))


    for i in range(len(percentiles) - 1):
        print(f'Std percentiles {percentiles[i]} to {percentiles[i + 1]}')

        selected_data = data[(preds_std > percentile_stds[i]) & (preds_std <= percentile_stds[i + 1])]
        print(selected_data[args.activity_column].value_counts())

        activity_classes = selected_data[args.activity_column].unique()
        if len(activity_classes) == 1:
            continue

        roc_auc = roc_auc_score(selected_data[args.activity_column], selected_data[pred_column])
        prc_auc = average_precision_score(selected_data[args.activity_column], selected_data[pred_column])

        print(f'ROC-AUC = {roc_auc:.3}')
        print(f'PRC-AUC = {prc_auc:.3}')
        print()


if __name__ == '__main__':
    evaluate_ensemble_confidence(Args().parse_args())
