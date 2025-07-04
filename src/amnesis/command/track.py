from amnesis.repository import Repository
from amnesis.snapshot.index import Index


def track():
    """
    Track files in the current experiment.
    """
    # Check if the current directory is a repository
    repository = Repository()
    if not repository.in_repository():
        raise RuntimeError(
            "Not in an amnesis repository. Run `amnesis init` to initialize a new repository."
        )

    # Get the index of the repository
    index = Index(repository.get_root())

    index_entry = index.read_index()
    if not index_entry:
        raise RuntimeError("No files to track. Please add files first.")

    print("Tracked files:")
    for entry in index_entry:
        print(f"\t{entry.path}")
