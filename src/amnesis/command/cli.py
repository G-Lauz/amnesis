from typing import Optional

import clipy

from amnesis.command.delete import deleteExperiment, deleteModel
from amnesis.repository import Repository

from .add import add
from .initialization import init
from .list_experiments import list_experiments
from .list_models import list_models
from .track import track


@clipy.App(
    usage="amnesis [OPTIONS] COMMAND [ARGS] ...",
    description="A local experiments tracking tool",
)
@clipy.Command(
    name="init", usage="amnesis init", description="Initialize a new amnesis project"
)
@clipy.Command(
    name="info",
    usage="amnesis info",
    description="Show information about the current project",
)
@clipy.Command(
    name="models",
    usage="amnesis models",
    description="List all models",
    subcommands=[
        clipy.Command(
            name="delete",
            usage="amnesis models delete [model_name]",
            description="Delete a model",
            options=[clipy.Option(name="model_name", positional=True, type=str)],
        ),
    ],
)
@clipy.Command(
    name="list",
    usage="amnesis list [--short]",
    description="List all experiments",
    options=[
        clipy.Option(name="short", action="store_true", required=False),
        clipy.Option(name="sort", type=str, nargs="+", default=None, required=False),
    ],
)
@clipy.Command(
    name="experiments",
    usage="amnesis experiments",
    description="List all experiments",
    options=[
        clipy.Option(name="model", type=str, default=None, required=False),
        clipy.Option(
            name="hyperparameters", action="store_true", default=False, required=False
        ),
        clipy.Option(
            name="metrics", action="store_true", default=False, required=False
        ),
        clipy.Option(name="sort", type=str, nargs="+", default=None, required=False),
    ],
    subcommands=[
        clipy.Command(
            name="delete",
            usage="amnesis experiments delete [hash]",
            description="Delete an experiment by hash",
            options=[clipy.Option(name="experiment hash", positional=True, type=str)],
        ),
    ],
)
@clipy.Command(
    name="delete",
    usage="amnesis delete [model | experiment] [model_name | experiment_hash]",
    description="Delete a model or an experiment",
    options=[
        clipy.Option(
            name="type", choices=["model", "experiment"], positional=True, type=str
        ),
        clipy.Option(name="id", positional=True, type=str),
    ],
)
@clipy.Command(
    name="add",
    usage="amnesis add [FILE]...",
    description="Track files with the next experiment",
    options=[
        clipy.Option(
            name="files",
            type=str,
            positional=True,
            nargs="+",
            default=None,
        ),
    ],
)
@clipy.Command(
    name="track",
    usage="amnesis track",
    description="Get a list of all tracked files",
)
def main(command: clipy.CommandDefinition):
    command_name = command.name
    options = command.options

    repository = Repository()
    in_repository = repository.in_repository()

    if not in_repository and command_name != "init":
        print(
            "Not in an amnesis repository. Run `amnesis init` to initialize a new repository."
        )
        return

    if command_name == "init":
        init(repo=repository)
    elif command_name == "info":
        raise NotImplementedError
    elif command_name == "models":
        if subcommand := test_subcommand(command, "delete"):
            deleteModel(repository, subcommand.options["model_name"])

        list_models(repo=repository)

    elif command_name == "experiments":
        if subcommand := test_subcommand(command, "delete"):
            deleteExperiment(repository, subcommand.options["experiment hash"])

        list_experiments(
            repo=repository,
            model_name=options["model"],
            hyperparameters=options["hyperparameters"],
            metrics=options["metrics"],
            sort=options["sort"],
        )
    elif command_name == "list":
        short_desc = options["short"]
        list_experiments(
            repo=repository,
            model_name=None,
            hyperparameters=not short_desc,
            metrics=not short_desc,
            sort=options["sort"],
        )
    elif command_name == "delete":
        if options["type"] == "model":
            deleteModel(repository, options["id"])
        else:  # elif options["type"] == "experiment":
            deleteExperiment(repository, options["id"])

    elif command_name == "add":
        if options["files"] is None:
            print("No files to add")
            return

        add(options["files"])

    elif command_name == "track":
        track()

    else:
        print(f"Unknown command: {command_name}")


def get_subcommand(
    command: clipy.CommandDefinition,
) -> Optional[clipy.CommandDefinition]:
    return command.subcommands[0] if command.subcommands else None


def test_subcommand(
    command: clipy.CommandDefinition, subcommand_name: str
) -> Optional[clipy.CommandDefinition]:
    subcommand = get_subcommand(command)
    if subcommand and subcommand.name == subcommand_name:
        return subcommand
    return None
