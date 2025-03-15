import functools
import sys
import traceback
from typing import List, Optional, TypedDict
import warnings

from .experiment_context import ExperimentContext

color_warning = lambda s: f"\033[93m{s}\033[0m"


class capture:
    """
    Original authors: Pietro Berkes, Andrea Maffezzoli --- https://code.activestate.com/recipes/577283-decorator-to-expose-local-variables-of-a-function-/
    Capture the local variables of the decorated function
    """

    def __init__(self, func):
        self._func = func

    def __call__(self, *args, **kwargs):
        self._capt_locals = None
        res = None

        def tracer(frame, event, arg):
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


class remember(ExperimentContext):
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

    def __init__(
        self,
        model_name: str,
        experiment_name: str = None,
        log: Optional[Log] = None,
        quick=False,
    ):
        """
        :param model_name: name of the model
        :param experiment_name: name of the experiment. If None, a name will be automatically generated
        :param log: dictionary containing lists of hyperparameters and metrics to log automatically. Artefacts and other parameters must be logged manually.
        :param quick: if True, disables automatic logging of local variables using a profiler. Enabling this flag requires you to log your metrics and other parameters manually.
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

    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._auto_log_params()
        super().__exit__(exc_type, exc_value, traceback)

        return False

    def _auto_log_params(self):
        if self._exp_locals:
            for log_type, vars in self._log.items():
                for param in vars:
                    if not isinstance(param, str):
                        continue

                    try:
                        value = self._exp_locals[param]
                    except:
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
            with self as ctx:
                if self._log:
                    experiment, self._exp_locals = capture(func)(ctx, *args, **kwargs)
                    return experiment
                else:
                    return func(ctx, *args, **kwargs)

        return wrapper
