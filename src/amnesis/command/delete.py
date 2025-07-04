"""
Deletion commands. Much wow
"""

# pylint: disable=C0103
# pylint: disable=W0622
# pylint: disable=W0718

import abc
from typing import Callable

from amnesis.repository import Repository


class delete(abc.ABC):
    """
    Abstract base class for delete commands.
    Creating the object calls the deletion (__call__) method.
    Use subclasses as functions
    """

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance(*args, **kwargs)  # Automatically trigger __call__()
        return instance

    def _exec(self, del_fn: Callable[[], str], id: str):
        try:
            del_fn(id)
            print(f"\033[92m{id} successfully deleted\033[0m\n")
        except Exception as e:
            print(f"\033[93m{e}\033[0m\n")

    def __call__(self, repository: Repository, id: str, *args, **kwds):
        pass


class deleteModel(delete):
    """
    Delete a model from the repository.
    """

    def __call__(self, repository: Repository, id: str, *args, **kwds):
        super()._exec(repository.remove_model, id)


class deleteExperiment(delete):
    """
    Delete an experiment (by hash) from the repository.
    """

    def __call__(self, repository: Repository, id: str, *args, **kwds):
        super()._exec(repository.remove_experiment, id)
