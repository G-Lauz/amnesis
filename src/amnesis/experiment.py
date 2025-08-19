import dataclasses
import hashlib
import json
import pathlib


@dataclasses.dataclass(order=True)
class Experiment:
    git: str

    model_name: str
    name: str
    tree: str
    parent: str

    date: str
    time: float
    hyperparameters: dict
    metrics: dict

    def __hash__(self):
        digest = self.hash()
        return int(digest, 16)

    def hash(self):
        """
        Returns the hash of the experiment as a hexadecimal string.
        This is a 40-character string representing the SHA-256 hash of the experiment.
        """
        self.hyperparameters = dict(sorted(self.hyperparameters.items()))
        self.metrics = dict(sorted(self.metrics.items()))

        data = {
            "git": self.git,
            "tree": self.tree,
            "hyperparameters": self.hyperparameters,
            "metrics": self.metrics,
        }
        data = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def save(self, path: pathlib.Path):
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as file:
            json.dump(dataclasses.asdict(self), file, indent=4)

    @classmethod
    def load(cls, path: pathlib.Path):
        with path.open() as file:
            metadata = json.load(file)

        return cls(**metadata)
