import datetime
import pathlib
import shutil
import time
from typing import Dict, List, Tuple

from .experiment import Experiment
from .manifest import Manifest, ManifestEntry
from .model import ModelSerializer
from .repository import Repository
from .snapshot.objects import ObjectStore
from .snapshot.snapshot import Snapshot
from .utils import generate_name


class ExperimentContext:
    repository: Repository

    hyperparameters: Dict[str, any]
    metrics: Dict[str, any]

    artifact_buffer: List[pathlib.Path]
    model_buffer: List[Tuple[any, ModelSerializer]]

    def __init__(self, model_name: str, experiment_name: str = None):
        self.repository = Repository()

        if not self.repository.in_repository():
            raise RuntimeError(
                "Not in an amnesis repository. Run `amnesis init` to initialize a new repository."
            )

        self.model_name = model_name
        self.experiment_name = experiment_name

        self.hyperparameters = {}
        self.metrics = {}

        self.artifact_buffer = []
        self.model_buffer = []

        self.obj_store = ObjectStore(self.repository.get_amnesis_dir() / "objects")

    def __enter__(self):
        if not self.experiment_name:
            self.experiment_name = self._generate_name()

        if self._experiment_name_exist(self.experiment_name):
            raise ValueError("Experiment name already exists")

        # Create model directory
        self.model_dir = self.repository.get_amnesis_dir() / self.model_name
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.time = time.perf_counter()
        self.date = datetime.datetime.now()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.time = round(time.perf_counter() - self.time, 6)
        self.date = self.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        snapshot = Snapshot(self.repository.root, self.model_dir, ignore=None)
        tree_obj = snapshot.create_snapshot()

        manifest = Manifest(self.model_dir)

        parent_hash = None
        manifest_entries = manifest.read_manifest()
        if manifest_entries:
            last_experiment = manifest_entries[-1]
            parent_hash = last_experiment.sha1

        experiment = Experiment(
            git="TODO",  # TODO: Implement git tracking
            model_name=self.model_name,
            name=self.experiment_name,
            tree=tree_obj.hash(),
            parent=parent_hash,
            date=self.date,
            time=self.time,
            hyperparameters=self.hyperparameters,
            metrics=self.metrics,
        )

        if experiment.hash() == parent_hash:
            print("Experiment is identical to the previous one. Not saving it.")
            return

        # Update the manifest
        manifest_entry = ManifestEntry(
            date=self.date, name=self.experiment_name, sha1=experiment.hash()
        )
        manifest.add(manifest_entry)

        # Create experiment directory
        experiment_dir = self.model_dir / experiment.hash()
        experiment_dir.mkdir(parents=True, exist_ok=True)

        experiment.save(experiment_dir / "metadata.json")
        self._save_artifacts(experiment_dir)
        self._save_models(experiment_dir)

    def log_hyperparameter(self, name, hyperparameter):
        self.hyperparameters[name] = hyperparameter

    def log_metric(self, name, metric):
        self.metrics[name] = metric

    def log_artifact(self, artifact: pathlib.Path):
        self.artifact_buffer.append(artifact)

    def _save_artifacts(self, experiment_dir: pathlib.Path):
        for artifact in self.artifact_buffer:
            name = artifact.name
            is_dir = artifact.is_dir()

            artifact_dir = experiment_dir / "artifacts"

            artifact_dir.mkdir(parents=True, exist_ok=True)

            if is_dir:
                shutil.copytree(artifact, artifact_dir / name)
            else:
                shutil.copy2(artifact, artifact_dir / name)

    def log_model(self, model, serializer: ModelSerializer):
        self.model_buffer.append((model, serializer))

    def _save_models(self, experiment_dir: pathlib.Path):
        for model, serializer in self.model_buffer:
            model_path = experiment_dir / "model"
            serializer.save(model, model_path)

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
        experiments = self.repository.get_experiments(self.model_name)

        if experiments is None:
            return False

        for experiment in experiments:
            if experiment.name == name:
                return True

        return False
