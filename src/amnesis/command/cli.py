import clipy

from amnesis.command.delete import deleteExperiment, deleteModel
from amnesis.repository import Repository

from .initialization import init
from .list_experiments import list_experiments
from .list_models import list_models


class ModelsCommand(clipy.Command):
    """
    Manage models in the repository
    """

    # TODO: the docstring description should be used instead
    # description = "Manage models in the repository"

    repo: Repository

    def __init__(self):
        super().__init__()
        self.repo = None

    def set_repository(self, repo: Repository):
        self.repo = repo

    def __call__(self):
        list_models(repo=self.repo)

    @clipy.Command()
    def delete(self, model_name: str):
        """
        Delete a model from the repository.

        Args:
            model_name (str): The name of the model to delete
        """
        deleteModel(Repository(), model_name)


class ExperimentsCommand(clipy.Command):
    """
    Manage experiments in the repository
    """

    repo: Repository

    def __init__(self):
        super().__init__()
        self.repo = None

    def set_repository(self, repo: Repository):
        self.repo = repo

    def __call__(
        self,
        model: str = None,
        hyperparameters: bool = False,
        metrics: bool = False,
        sort: list[str] = None,
    ):
        """
        List experiments in the repository,
        optionally filtering by model name and showing hyperparameters and metrics.

        Args:
            model: The name of the model to filter experiments by.
            hyperparameters: Whether to show hyperparameters for each experiment.
            metrics: Whether to show metrics for each experiment.
            sort: A list of fields to sort the experiments by.
        """
        list_experiments(
            repo=self.repo,
            model_name=model,
            hyperparameters=hyperparameters,
            metrics=metrics,
            sort=sort,
        )

    @clipy.Command()
    def delete(self, experiment_uuid: str):
        """
        Delete an experiment from the repository.

        Args:
            experiment_uuid (str): The uuid of the experiment to delete
        """
        deleteExperiment(Repository(), experiment_uuid)


class Amnesis(clipy.Command):
    """
    A local experiments tracking tool
    """

    repo: Repository
    in_repo: bool

    models: ModelsCommand = ModelsCommand()
    experiments: ExperimentsCommand = ExperimentsCommand()

    def __init__(self):
        super().__init__()

        self.repo = Repository()
        self.in_repo = self.repo.in_repository()

        self.models.set_repository(self.repo)
        self.experiments.set_repository(self.repo)

    def _check_if_in_repository(self):
        if not self.in_repo:
            print(
                "Not in an amnesis repository. Run `amnesis init` to initialize a new repository."
            )
            return False
        return True

    @clipy.Command
    def init(self):
        """
        Inistialize a new amnesis project
        """
        init(repo=self.repo)

    @clipy.Command
    def info(self):
        """
        Show information about the current project
        """
        self._check_if_in_repository()
        raise NotImplementedError

    @clipy.Command
    def list(self, short: bool = False, sort: list[str] = None):
        """
        List all experiments

        Args:
            short: If True, only show a short description of each experiment.
            sort: A list of fields to sort the experiments by.
        """
        if not self._check_if_in_repository():
            return

        list_experiments(
            repo=self.repo,
            model_name=None,
            hyperparameters=not short,
            metrics=not short,
            sort=sort,
        )

    @clipy.Command
    def delete(self, type: str, id: str):
        """
        Delete a model or an experiment

        Args:
            type: The type of the item to delete, either "model" or "experiment".
            id: The name of the model or the uuid of the experiment to delete.
        """
        if not self._check_if_in_repository():
            return

        # check if type is valid
        if type not in ["model", "experiment"]:
            print(f"Unknown type: {type}. Type must be either 'model' or 'experiment'.")
            return

        if type == "model":
            deleteModel(self.repo, id)
        elif type == "experiment":
            deleteExperiment(self.repo, id)
        else:
            print(f"Unknown type: {type}. Type must be either 'model' or 'experiment'.")


def main():
    cli = Amnesis()
    cli()
