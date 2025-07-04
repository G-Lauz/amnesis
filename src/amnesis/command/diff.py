from typing import Set

from amnesis.repository import Repository
from amnesis.snapshot.diff import DiffEngine
from amnesis.snapshot.objects import ObjectStore
from amnesis.snapshot.tree import Tree, TreeEntry


def get_entries(repository: Repository, tree: Tree) -> Set[TreeEntry]:
    obj_store = ObjectStore(repository.root / ".amnesis" / "objects")

    tree_obj = obj_store.read(tree)
    tree = Tree(repository.index, ignore=None)
    entries = tree.read_tree(tree_obj)

    return set(entries)


def get_common_files_entries(
    entries1: Set[TreeEntry], entries2: Set[TreeEntry]
) -> Set[TreeEntry]:
    common_entries = set()

    for entry in entries2:
        for old_entry in entries1:
            if entry.path == old_entry.path:
                common_entries.add((entry, old_entry))
                break

    return common_entries


def diff(repository: Repository, hash1, hash2):
    """
    Compare two experiments and print the differences.
    """
    if not repository.in_repository():
        print(
            "Not in an amnesis repository. Run `amnesis init` to initialize a new repository."
        )
        return

    exp1 = repository.get_experiment(hash1)
    exp2 = repository.get_experiment(hash2)

    if exp1 is None:
        print(f"Experiment {hash1} not found.")
        return

    if exp2 is None:
        print(f"Experiment {hash2} not found.")
        return

    entries1 = get_entries(repository, exp1.tree)
    entries2 = get_entries(repository, exp2.tree)

    common_entries = get_common_files_entries(entries1, entries2)
    added_entries = entries2 - common_entries
    removed_entries = entries1 - common_entries

    diff_engine = DiffEngine(repository.root)

    for entry1, entry2 in common_entries:
        content1 = diff_engine.restore_patch(entry1.sha1)
        content2 = diff_engine.restore_patch(entry2.sha1)

        chunks = diff_engine.compute_patch(content1, content2)

        if chunks:
            unified_diff = diff_engine.format_unified(
                chunks, content1, fromfile=hash2, tofile=hash1
            )
            print(f"Changes in {entry1.path}:")
            print(unified_diff)
