from typing import List, Optional

from amnesis.experiment import Experiment
from amnesis.repository import Repository


class DataFrame:
    """
    A class that represent data in a table format.

    It allow concatenation of dataframes and display of the data in a table format.
    """

    def __init__(self, columns: list, data: list):
        self.columns = columns
        self.data = data

    def __add__(self, other):
        """
        Add the columns of the other dataframe to the current dataframe if it does not already exist.
        The rows are assumed to be in the same order. If the columns are not in the same order, the data will be
        misaligned.
        """
        duplicate_columns = [col for col in other.columns if col in self.columns]

        other_columns = [col for col in other.columns if col not in duplicate_columns]

        self.columns += other_columns

        if not self.data:
            self.data = other.data
            return self

        for i, _ in enumerate(self.data):
            self.data[i] += [
                other.data[i][other.columns.index(col)] for col in other_columns
            ]

        return self

    def __str__(self):
        max_len = [
            max([len(str(row[i])) for row in self.data] + [len(self.columns[i])])
            for i in range(len(self.columns))
        ]

        header = " | ".join(
            [f"{col:<{max_len[i]}}" for i, col in enumerate(self.columns)]
        )
        separator = "-+-".join(["-" * length for length in max_len])

        lines = [header, separator]

        for row in self.data:
            line = " | ".join([f"{row[i]:<{max_len[i]}}" for i in range(len(row))])
            lines.append(line)

        return "\n".join(lines)

    def sort(self, columns: str):
        """
        Sort the data by the values in the column or columns.
        Precedence follows the sequence of columns passed by the user
        """
        column_indices = [self.columns.index(c) for c in columns]
        self.data = sorted(self.data, key=lambda x: tuple(x[i] for i in column_indices))


def get_model_names(repo: Repository):
    try:
        models = repo.get_models()
    except FileNotFoundError as error:
        print(error)

    return [model.name for model in models]


def get_experiment_info_frame(experiments: List[Experiment]):
    columns = ["model", "experiment", "date", "hash"]
    data = []
    for experiment in experiments:
        data.append(
            [experiment.model_name, experiment.name, experiment.date, experiment.hash()]
        )

    return DataFrame(columns, data)


def get_hyperparameters_frame(experiments: List[Experiment]):
    # fetch all unique hyperparameters
    hyperparameters = set()
    for experiment in experiments:
        hyperparameters.update(experiment.hyperparameters.keys())
    hyperparameters = sorted(list(hyperparameters))

    columns = ["model", "experiment"] + list(hyperparameters)
    data = []
    for experiment in experiments:
        row = [experiment.model_name, experiment.name]
        for hp in hyperparameters:
            row.append(experiment.hyperparameters.get(hp, ""))
        data.append(row)

    return DataFrame(columns, data)


def get_metrics_frame(experiments: List[Experiment]):
    # fetch all unique metrics
    metrics = set()
    for experiment in experiments:
        metrics.update(experiment.metrics.keys())
    metrics = sorted(list(metrics))

    columns = ["model", "experiment"] + list(metrics)
    data = []
    for experiment in experiments:
        row = [experiment.model_name, experiment.name]
        for metric in metrics:
            row.append(experiment.metrics.get(metric, ""))
        data.append(row)

    return DataFrame(columns, data)


def match_columns(columns: List[str], frame: DataFrame):
    for c in columns:
        if c not in frame.columns:
            return False, c

    return True, None


def list_experiments(
    repo: Repository,
    model_name: str = None,
    hyperparameters: bool = False,
    metrics: bool = False,
    sort: Optional[List[str]] = None,
):
    models_name = get_model_names(repo)

    if model_name is not None and model_name not in models_name:
        print(f"Model {model_name} not found. Try `amnesis models` to list all models.")
        return

    models = [model_name] if model_name in models_name else models_name

    experiments = []
    for model in models:
        experiments += repo.get_experiments(model)

    # Empty frame
    frame = DataFrame([], [])

    if not (hyperparameters or metrics):
        frame = get_experiment_info_frame(experiments)

    if hyperparameters:
        hp_frame = get_hyperparameters_frame(experiments)
        frame += hp_frame

    if metrics:
        metrics_frame = get_metrics_frame(experiments)
        frame += metrics_frame

    if sort:
        if not (matches := match_columns(sort, frame))[0]:
            print(
                f"Column {matches[1]} not found in the dataframe. Available columns are: {', '.join(frame.columns)}"
            )
            return
        frame.sort(sort)

    print(frame)
