import functools
import sys
import traceback
import warnings
from copy import copy
from typing import List, Optional, TypedDict

from .experiment_context import ExperimentContext

color_warning = lambda s: f"\033[93m{s}\033[0m"  # pylint: disable=unnecessary-lambda-assignment


class capture:  # pylint: disable=invalid-name
    """
    Original authors: Pietro Berkes, Andrea Maffezzoli
    --- https://code.activestate.com/recipes/577283-decorator-to-expose-local-variables-of-a-function-/
    Capture the local variables of the decorated function
    """

    def __init__(self, func):
        self._func = func

    def __call__(self, *args, **kwargs):
        self._capt_locals = None
        res = None

        def tracer(frame, event, _):
            if event == "return":
                self._capt_locals = frame.f_locals.copy()

        sys.setprofile(tracer)
        try:
            res = self._func(*args, **kwargs)
        except Exception as e:
            warnings.warn(
                color_warning(
                    f"\nFailed to run and/or save metrics.\nError: {e}\n\nIf the error is with the logging, make sure your \
                    Python implementaion supports profiling or please log your metrics and other parameters manually."
                )
            )
            traceback.print_exception(e)
            raise e

        finally:
            sys.setprofile(None)

        ret_locals = self._capt_locals
        del self._capt_locals

        return res, ret_locals


class remember(ExperimentContext):  # pylint: disable=invalid-name
    """
    Wraps the decorated function with the Experiment context manager
    Automatically logs hyperparameters and other metrics if requested
    """

    class Log(TypedDict):
        """
        Typed dict for specifying which metrics to log automatically
        Only Hyperparameters and Metrics are supported for now
        Log Artefacts and other parameters manually
        """

        hyperparams: List[str]
        metrics: List[str]

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        model_name: str,
        experiment_name: str = None,
        log: Optional[Log] = None,
        quick=False,
        is_fn_singleton=True,
    ):
        """
        :param model_name:      name of the model
        :param experiment_name: name of the experiment.
                                If None, a name will be automatically generated
        :param log:             dictionary containing lists of hyperparameters and metrics to log automatically.
                                Artefacts and other parameters must be logged manually.
        :param quick:           if True, disables automatic logging of local variables using a profiler.
                                Enabling this flag requires you to log your metrics and other parameters manually.
        :param is_fn_singleton: if True, the decorator is only constructed once and acts as expected for decorator behavior,
                                i.e., reuses the experiment context across multiple calls of the decorated function.<br />
                                If False, a copy of the decorator is created for each function call, which allows for different
                                experiment contexts to be used for a same model (different metrics, hyperparams, etc.)<br />
                                If False, the experiment name will be ignored and a random name will be generated for each call.

                                `# TODO: keep the original experiment name in the context and add a version number when creating a copy.`
        """
        super().__init__(model_name, experiment_name)
        if log and quick:
            warnings.warn(
                color_warning(
                    "Quick mode is enabled. Logging with profiler will be disabled.\
                     Please log your metrics and other parameters manually."
                )
            )

        self._log = log if not quick else None
        self._exp_locals = None
        self._fn_singleton = is_fn_singleton

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):  # pylint: disable=redefined-outer-name
        self._auto_log_params()
        super().__exit__(exc_type, exc_value, traceback)

        return False

    def _auto_log_params(self):
        if self._exp_locals:
            for log_type, vars in self._log.items():  # pylint: disable=redefined-builtin
                for param in vars:
                    if not isinstance(param, str):
                        continue

                    try:
                        value = self._exp_locals[param]
                    except:  # pylint: disable=bare-except
                        warnings.warn(color_warning(f"{log_type[:-1].capitalize()} {param} not found in the experiment. Skipping."))
                        continue

                    match log_type:
                        case "hyperparams":
                            self.log_hyperparameter(param, value)
                        case "metrics":
                            self.log_metric(param, value)
                        case _:
                            pass

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # a shallow copy should do, since no metrics, artefacts, hyperparameters, etc. were logged yet... Unique IDs will be regenerated
            instance = self if self._fn_singleton else copy(self)

            with instance as ctx:
                if instance._log:  # pylint: disable=protected-access
                    experiment, instance._exp_locals = capture(func)(ctx, *args, **kwargs)
                    return experiment
                else:
                    return func(ctx, *args, **kwargs)

        return wrapper

    def __copy__(self):
        """
        Create a shallow copy of the remember decorator (including existing data/metrics).
        The experiment context will have a different uuid and a randomly generated experiment name.
        """
        if self._fn_singleton:
            raise RuntimeError("Cannot copy a singleton `remember` decorator. Set `remember(..., is_fn_singleton=False)` to allow copying.")

        # Dummy object to generate new identifiers
        context = ExperimentContext.copy_context_data(self)

        cls = type(self)
        cpy = cls.__new__(cls)
        cpy.__dict__.update(self.__dict__)

        # ExperimentContext unique data should be different. Metrics and artefacts will be stored in a different dir in .amnesis
        cpy.__dict__.update(context.__dict__)

        return cpy
