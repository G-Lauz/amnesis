import os
import pathlib
import shutil

from .experiment import Experiment
from .snapshot.index import Index


class Repository:
    def __init__(self):
        self.root = None
        self.dir_name = ".amnesis"

        self.root = self.get_root()

        if self.root:
            self.index = Index(self.root)

    def init(self, path: pathlib.Path = None):
        if path is None:
            path = pathlib.Path.cwd()

        repository_dir = path / self.dir_name

        if repository_dir.exists():
            raise FileExistsError(f"Repository already exists in {path}")

        self.root = path
        repository_dir.mkdir(parents=True, exist_ok=True)

        self.index = Index(self.root)

    def in_repository(self):
        path = pathlib.Path.cwd()
        return self._get_root_path(path) is not None

    def get_root(self):
        path = pathlib.Path.cwd()
        return self._get_root_path(path)

    def get_amnesis_dir(self):
        if self.in_repository():
            return self.get_root() / self.dir_name

        if self.root:
            return self.root / self.dir_name

        raise FileNotFoundError("Cannot find `.amnesis` directory")

    def get_models(self):
        amnesis_dir = self.get_amnesis_dir()

        models = []
        for model in amnesis_dir.iterdir():
            if model.is_dir():
                models.append(model)

        if models:
            return models

        return None

    def remove_model(self, model_name: str):
        try:
            shutil.rmtree(self.get_amnesis_dir() / model_name, ignore_errors=False)
        except FileNotFoundError:
            raise FileNotFoundError(f"Model {model_name} not found")
        # OSError exceptions can still be thrown. e.g., permission dernied, resource busy, etc.

    def get_experiment(self, experiment_hash: str) -> Experiment | None:
        models = self.get_models()

        if models is None:
            return None

        for model in models:
            experiments = self.get_experiments(model.name)

            if experiments is None:
                continue

            for experiment in experiments:
                if experiment.hash() == experiment_hash:
                    return experiment

        return None

    def get_experiments(self, model_name: str):
        models = self.get_models()

        if models is None:
            return None

        models_names = [model.name for model in models]

        if model_name not in models_names:
            return None

        experiments = []
        model_dir = self.get_amnesis_dir() / model_name

        for experiment in model_dir.iterdir():
            experiment_metadata = experiment / "metadata.json"
            if experiment.is_dir() and experiment_metadata.exists():
                experiments.append(Experiment.load(experiment_metadata))

        return experiments

    def remove_experiment(self, experiment_hash: str):
        models = self.get_models()

        if models is None:
            raise FileNotFoundError("No models found")

        for model in models:
            experiments = [exp.hash() for exp in self.get_experiments(model.name)]

            if experiment_hash in (experiments or []):
                self.remove_experiment_by_model(model.name, experiment_hash)
                return

        raise FileNotFoundError(f"Experiment {experiment_hash} not found")

    def remove_experiment_by_model(self, model_name: str, experiment_hash: str):
        try:
            shutil.rmtree(
                self.get_amnesis_dir() / model_name / experiment_hash,
                ignore_errors=False,
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Experiment {experiment_hash} not found")
        # OSError exceptions can still be thrown. e.g., permission dernied, resource busy, etc.

    def _get_root_path(self, path: pathlib.Path):
        if self.root:
            return self.root

        repository_dir = path / self.dir_name
        if repository_dir.exists():
            self.root = path
            return path

        path = path.parent
        if os.path.abspath(path) == os.path.abspath(os.sep):
            return None

        return self._get_root_path(path)
