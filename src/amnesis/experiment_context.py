import datetime
import pathlib
import shutil
import time
import uuid
from typing import Dict

from .experiment import Experiment
from .model import ModelSerializer
from .repository import Repository
from .utils import generate_name


class ExperimentContext:
    repository: Repository
    experiment: Experiment

    hyperparameters: Dict[str, any]
    metrics: Dict[str, any]

    def __init__(self, model_name: str, experiment_name: str = None):
        self.repository = Repository()

        self.experiment = Experiment(
            git="self.git.head",  # TODO: get git head
            model_name=model_name,
            name=None,
            uuid=uuid.uuid4().hex,
            date=None,
            time=None,
            hyperparameters={},
            metrics={},
        )

        if not experiment_name:
            experiment_name = self._generate_name()

        if self._experiment_name_exist(experiment_name):
            raise ValueError("Experiment name already exists")

        self.experiment.name = experiment_name

        self.hyperparameters = {}
        self.metrics = {}

        # Create model directory
        self.model_dir = self.repository.get_amnesis_dir() / model_name
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        self.experiment_dir = self.model_dir / self.experiment.uuid
        self.experiment_dir.mkdir(parents=True, exist_ok=True)

        self.time = time.perf_counter()
        self.date = datetime.datetime.now()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.time = round(time.perf_counter() - self.time, 6)

        self.save_metadata()

    def save_metadata(self):
        self.experiment.date = self.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.experiment.time = self.time
        self.experiment.hyperparameters = self.hyperparameters
        self.experiment.metrics = self.metrics

        self.experiment.save(self.experiment_dir / "metadata.json")

    def log_model(self, model, serializer: ModelSerializer):
        model_path = self.experiment_dir / "model"
        serializer.save(model, model_path)

    def log_hyperparameter(self, name, hyperparameter):
        self.hyperparameters[name] = hyperparameter

    def log_metric(self, name, metric):
        self.metrics[name] = metric

    def log_artifact(self, artifact: pathlib.Path):
        name = artifact.name
        is_dir = artifact.is_dir()

        artifact_dir = self.experiment_dir / "artifacts"

        artifact_dir.mkdir(parents=True, exist_ok=True)

        if is_dir:
            shutil.copytree(artifact, artifact_dir / name)
        else:
            shutil.copy2(artifact, artifact_dir / name)

    def _generate_name(self):
        attempts = 0

        name = generate_name()
        while self._experiment_name_exist(name):
            if attempts > 42:
                raise TimeoutError(
                    "It looks like you are very unlucky and/or you do have a large "
                    "number of versions. You can avoid this issue by manually "
                    "naming your version, or you can clean your project by deleting "
                    "unused versions."
                )

            name = generate_name()
            attempts += 1

        return name

    def _experiment_name_exist(self, name):
        experiments = self.repository.get_experiments(self.experiment.model_name)

        if experiments is None:
            return False

        for experiment in experiments:
            if experiment.name == name:
                return True

        return False
