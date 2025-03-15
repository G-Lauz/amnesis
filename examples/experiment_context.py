import pathlib
import time

import matplotlib.pyplot as plt
import numpy

from amnesis import ExperimentContext, ModelSerializer, remember


class NumpySerializer(ModelSerializer):
    def save(self, model, path):
        numpy.save(path, model)

    def load(self, path):
        return numpy.load(path)


def my_cool_experiment(experiment):
    print("Running experiment...")

    # Mock experiment
    time.sleep(1)

    # Mock model
    model = numpy.random.rand(10, 10)

    # save sinusoide plot artifact
    x = numpy.linspace(0, 2 * numpy.pi, 100)
    y = numpy.sin(x)
    plt.plot(x, y)

    output_path = pathlib.Path("./output/sinusoide.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(str(output_path))
    experiment.log_artifact(output_path)

    # Save a folder as artifact
    folder_path = pathlib.Path("./output/folder")
    subfolder_path = folder_path / "subfolder"
    subfolder_path.mkdir(parents=True, exist_ok=True)

    with open(folder_path / "file1.txt", "w", encoding="utf8") as f:
        f.write("Hello, World!")

    with open(subfolder_path / "file2.txt", "w", encoding="utf8") as f:
        f.write("Hello, World!")

    experiment.log_artifact(folder_path)

    experiment.log_model(model, serializer=NumpySerializer())


def with_ctx():
    """
    Run an experiment using the ExperimentContext and manually log the hyperparameters and metrics using ExperimentContext methods
    """
    with ExperimentContext(model_name="with_ctx") as experiment:
        experiment.log_hyperparameter("hyper_param1", 0.01)
        experiment.log_hyperparameter("hyper_param2", 32)

        my_cool_experiment(experiment)

        experiment.log_metric("metric1", 0.95)
        experiment.log_metric("metric2", 0.75)


@remember(
    model_name="with_decorator",
    log={
        "hyperparams": ["hyper_param1", "hyper_param2"],
        "metrics": ["metric1", "metric2"],
    },
)
def with_decorator(experiment):
    """
    Run an experiment using the "remember" decorator, automatically wrapping the function with the ExperimentContext context manager,
    and automatically logging the hyperparameters and metrics using the specified variable names
    """
    hyper_param1 = 0.01
    hyper_param2 = 32

    metric1 = 0.95
    metric2 = 0.75

    my_cool_experiment(experiment)


if __name__ == "__main__":
    with_ctx()
    with_decorator()
