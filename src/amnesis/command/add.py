import pathlib
from typing import List, Union

from amnesis.repository import Repository
from amnesis.snapshot.index import Index


def add(files: List[Union[str, pathlib.Path]]):
    """
    Add files to the next experiment.

    Args:
        files (List[Union[str, pathlib.Path]]): List of files to add.
    """
    if not files:
        raise ValueError("No files provided to add.")

    # Check if the current directory is a repository
    repository = Repository()
    repository.validate_in_repository()

    # Get the index of the repository
    index = Index(repository.get_root())

    index.add(files)

    print("Files added successfully.")
