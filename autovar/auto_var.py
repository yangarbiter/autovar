import argparse
from argparse import RawTextHelpFormatter
import base64
from copy import deepcopy
import inspect
import time
from typing import Dict, Tuple, List, Any, Callable, Optional, Union
import re
import pprint
import logging
import gc

import git
import git.exc
from joblib import Parallel, delayed
from mkdir_p import mkdir_p
from sklearn.model_selection import ParameterGrid

from .base import default_fn_dict, default_val_dict, \
        ParameterAlreadyRanError, VariableValueNotSetError, \
        VariableNotRegisteredError

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def add_all_commit(repo, commit_msg="update"):
    repo.git.commit('-m', commit_msg)
    files = repo.git.diff(None, name_only=True)
    for f in files.split('\n'):
        repo.git.add(f)

class AutoVar(object):

    def __init__(self, before_experiment_hooks=None, after_experiment_hooks=None,
                 settings: Dict=None, logging_level: int=logging.WARNING) -> None:
        """
        settings : {
            'server_url': 'http://127.0.0.1:8080/nn_attack/',
            'result_file_dir': './results/'
            'file_format': 'json' or 'pickle'
        }
        """
        logger.setLevel(logging_level)

        self.experiments: Dict[str, Any] = {}
        self.variables: Dict[str, dict] = {}
        self.var_shown_name: Dict[str, Dict[str, str]] = {}
        self.var_description: Dict[str, str] = {}
        self.var_class: Dict[str, Any] = {}
        self.var_value: Dict[str, Any] = {}

        self.inter_var: Dict[str, Any] = {}
        self.result_fields: List[str] = []
        self.settings: Dict
        self.settings = {'file_format': 'json'}
        if isinstance(settings, dict):
            self.settings.update(settings)
        if ('result_file_dir' in self.settings) and self.settings['result_file_dir']:
            mkdir_p(self.settings['result_file_dir'])

        try:
            self.repo = git.Repo(search_parent_directories=True)
            self.var_value['git_hash'] = self.repo.head.object.hexsha
        except git.exc.InvalidGitRepositoryError:
            logger.warning("Git repository not found.")

        self.after_experiment_hooks = after_experiment_hooks
        self.before_experiment_hooks = before_experiment_hooks

        self._read_only: bool = False
        self._no_hooks: bool = False

    def set_logging_level(self, level: int):
        logger.setLevel(level)

    def add_variable_class(self, variable_class, var_name: str = None):
        if var_name is None:
            var_name = variable_class.__class__.var_name
            if var_name is None:
                var_name = type(variable_class).__name__

        if var_name in self.var_class:
            raise ValueError('Don\'t register class "{}" twice '.format(var_name))
        self.var_class[var_name] = variable_class
        #self.variables.setdefault(var_name, deepcopy(default_fn_dict))
        self.variables.update(variable_class.__class__.variables)
        self.var_shown_name.update(
                variable_class.__class__.variable_shown_name)

    def add_variable(self, var_name: str, dtype) -> None:
        d = deepcopy(default_val_dict)
        d['dtype'] = dtype
        self.variables.setdefault(var_name, d)

    def get_var_shown_name(self, var_name: str,
                           argument: Union[str, None] = None) -> str:
        if argument is None:
            argument = self.get_variable_name(var_name)
        for key, val in self.var_shown_name[var_name].items():
            if re.fullmatch(key, argument):
                argument = re.sub(key, val, argument)
        return argument

    def get_var(self, var_name: str, *args, **kwargs):
        """[summary]

        Arguments:
            var_name {[type]} -- [description]
            argument {[type]} -- [description]

        Raises:
            ValueError -- [description]
            ValueError -- [description]

        Returns:
            [type] -- [description]
        """
        if var_name not in self.variables:
            raise VariableNotRegisteredError('Variable "%s" not registered.' % var_name)
        if var_name not in self.var_value:
            raise VariableValueNotSetError('Value for variable "%s" is not assigned.' % var_name)
        argument = self.var_value[var_name]

        if self.variables[var_name]["type"] == "val":
            return argument
        else:
            if argument in self.variables[var_name]["argument_fn"]:
                func = self.variables[var_name]["argument_fn"][argument]
            else:
                m = None
                for arg_template, func in self.variables[var_name]["argument_fn"].items():
                    m = re.fullmatch(arg_template, argument)
                    if m is not None:
                        kwargs.update(m.groupdict())
                        break
                if m is None:
                    raise ValueError('Argument "%s" not matched in Variable '
                                     '"%s".' % (argument, var_name))

            kwargs['auto_var'] = self
            named_args = inspect.getfullargspec(func)[0]
            if 'var_value' in named_args:
                kwargs['var_value'] = self.var_value
            if 'inter_var' in named_args:
                kwargs['inter_var'] = self.inter_var
            return func(*args, **kwargs)

    def match_variable(self, var_name: str, argument):
        if argument is None:
            return False

        if self.variables[var_name]["type"] == "val":
            return True
        else:
            if argument in self.variables[var_name]["argument_fn"]:
                return True
            else:
                for arg_template in self.variables[var_name]["argument_fn"]:
                    m = re.fullmatch(arg_template, argument)
                    if m is not None:
                        return True
        return None

    def get_variable_value(self, var_name: str):
        logger.warn("Use get_variable_name instead.")
        if var_name not in self.var_value:
            raise ValueError(f"{var_name} not in var_value")
        return self.var_value[var_name]

    def get_variable_name(self, var_name: str):
        if var_name not in self.var_value:
            raise ValueError(f"{var_name} not in variable name")
        return self.var_value[var_name]

    def get_var_with_argument(self, var_name: str, argument: str, *args, **kwargs):
        if self.variables[var_name]["type"] == "val":
            return argument
        else:
            if argument in self.variables[var_name]["argument_fn"]:
                func = self.variables[var_name]["argument_fn"][argument]
            else:
                m = None
                for arg_template, func in self.variables[var_name]["argument_fn"].items():
                    m = re.fullmatch(arg_template, argument)
                    if m is not None:
                        kwargs.update(m.groupdict())
                        break
                if m is None:
                    raise ValueError('Argument "%s" not matched in Variable "%s".' % (argument, var_name))
            kwargs['auto_var'] = self
            named_args = inspect.getfullargspec(func)[0]
            if 'var_value' in named_args:
                kwargs['var_value'] = self.var_value
            if 'inter_var' in named_args:
                kwargs['inter_var'] = self.inter_var
            return func(*args, **kwargs)

    def get_intermidiate_variable(self, var_name: str):
        return self.inter_var[var_name]

    def set_variable_value(self, var_name: str, value) -> None:
        if self._read_only:
            raise ValueError("should not set variable value while read_only")
        #if var_name not in self.var_value:
        #    raise ValueError(f"{var_name} not in var_value")
        self.var_value[var_name] = value
        self._check_var_argument(var_name=var_name, argument=value)

    def set_intermidiate_variable(self, var_name: str, value) -> None:
        self.inter_var[var_name] = value

    def set_variable_value_by_dict(self, var_value: Dict[str, Any]) -> None:
        if self._read_only:
            raise ValueError("should not set variable value while read_only")
        for k, v in var_value.items():
            self.set_variable_value(k, v)

    def _run_before_hooks(self):
        if not self._no_hooks and self.before_experiment_hooks is not None:
            for hook_fn in self.before_experiment_hooks:
                try:
                    hook_fn(self)
                except ParameterAlreadyRanError:
                    logger.warning("The result for this parameter is "
                                        "already ran.")
                    return False
                except:
                    print("Error occur during running before hooks.")
                    raise
        return True

    def _run_after_hooks(self, ret):
        if not self._no_hooks and self.after_experiment_hooks is not None:
            for hook_fn in self.after_experiment_hooks:
                hook_fn(self, ret)

    def run_single_experiment(self, experiment_fn: Union[Callable[..., Any], str],
                              with_hook: bool=True,
                              verbose: int=0) -> bool:
        self._read_only = True
        if isinstance(experiment_fn, str):
            original_settings = deepcopy(self.settings)
            self.settings.update(self.experiments[experiment_fn]['settings'])

        try:
            if with_hook:
                ret = self._run_before_hooks()
            else:
                ret = True
            if ret:
                start_time = time.time()
                if isinstance(experiment_fn, str):
                    ret = self.experiments[experiment_fn]['fn'](self)
                else:
                    ret = experiment_fn(self)
                end_time = time.time()
                logger.info("Running time: %f", end_time - start_time)
                if isinstance(ret, dict):
                    ret['running_time'] = end_time - start_time
                else:
                    # return value is not dict
                    pass

                if with_hook:
                    self._run_after_hooks(ret)
        finally:
            self.inter_var.clear()
            self._read_only = False
            gc.collect()

        if isinstance(experiment_fn, str):
            self.settings = original_settings
        return ret

    def _check_var_argument(self, var_name: str, argument):
        if self.variables[var_name]["type"] != "val" \
            and not self.match_variable(var_name, argument):
                raise ValueError('Argument "%s" not in Variable "%s".' % (argument, var_name))
        elif self.variables[var_name]["type"] == "val" \
            and not isinstance(argument, self.variables[var_name]['dtype']):
            raise TypeError('Argument "%s" not in the correct type "%s".' % (
                            type(argument), self.variables[var_name]['dtype']))

    def _check_grid_params(self, grid_params: Dict[str, List]) -> bool:
        # TODO check duplicated params
        # TODO duplicated check var argument since set_param_value will check
        for k, v in grid_params.items():
            for i in v:
                self._check_var_argument(k, i)
        return True

    def run_grid_params(self,
                        experiment_fn: Union[Callable[..., Any], str],
                        grid_params: Union[Dict[str, List], List[Dict[str, List]]],
                        with_hook: bool=True,
                        max_params: int=-1,
                        commit_before_run: bool=False,
                        verbose: int=0,
                        allow_failure: bool=True,
                        n_jobs: int=-1,
                        backend: Optional[str]=None,
                        pre_dispatch: str='2 * n_jobs') -> Tuple[List, List]:

        if commit_before_run:
            if self.repo is None:
                raise ValueError("Not currently in git repo.")
            add_all_commit(self.repo)

        if isinstance(grid_params, list):
            ret_params: List = []
            for grid_param in grid_params:
                self._check_grid_params(grid_param)

                grid = ParameterGrid(grid_param)
                ret_params += list(grid)
        else:
            ret_params = list(ParameterGrid(grid_params))

        if max_params != -1:
            ret_params = ret_params[:max_params]

        parallel = Parallel(n_jobs=n_jobs, verbose=verbose,
                            backend=backend, pre_dispatch=pre_dispatch)

        def _helper(auto_var, params):
            auto_var.set_variable_value_by_dict(params)
            if verbose:
                logger.info("Running parameter:" + str(params))
            try:
                results = auto_var.run_single_experiment(
                    experiment_fn,
                    with_hook=(with_hook and (not self._no_hooks)),
                    verbose=verbose
                )
            except Exception as e:
                if allow_failure:
                    logger.error("Error with " + str(params))
                else:
                    raise e
                results = None

            return results

        with parallel:
            ret_results = parallel(delayed(_helper)(deepcopy(self), params)
                                   for params in ret_params)

        return ret_params, ret_results

    def summary(self) -> None:
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.variables)

    def generate_name(self) -> str:
        _ = hash(tuple(sorted(self.var_value.items())))
        return base64.b64encode(str(_).encode()).decode()

    def register_experiment(self, experiment_name: str,
                               experiment_fn: Callable[..., Any],
                               settings: Dict = None) -> None:
        if experiment_name in self.experiments:
            logger.info(f"Overriding experiment {experiment_name}")
        if settings is None:
            settings = dict()
        self.experiments[experiment_name] = {
            "fn": experiment_fn,
            "settings": settings,
        }


    def get_argparser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
        parser.add_argument('--no-hooks', required=False, action='store_true',
                            help="run without the hooks")

        if len(self.experiments) > 0:
            parser.add_argument('--experiment', type=str, required=True,
                                choices=[k for k in self.experiments.keys()],
                                help="The experiment to run")

        for var_name, v in self.variables.items():
            if v['type'] == 'choice':
                help_str = ''
                if self.var_class[var_name].__doc__ is not None:
                    help_str += self.var_class[var_name].__doc__ + "\n"
                help_str += "Options:\n"
                help_str += "\n".join(
                    ["  %s: %s" % (kk, vv.__doc__) for kk, vv in v['argument_fn'].items()])
                parser.add_argument(f'--{var_name}', type=str, required=True,
                                    action=make_action(self, var_name),
                                    help=help_str)
            else:
                parser.add_argument(f'--{var_name}', type=v['dtype'], required=True)

        return parser

    def parse_argparse(self, args: Optional[List[str]]=None):
        parser = self.get_argparser()
        parsed_args = parser.parse_args(args=args)
        self._no_hooks = parsed_args.no_hooks

        variables = vars(parsed_args)
        del variables['no_hooks']
        experiment_name = variables.pop('experiment', None)
        self.set_variable_value_by_dict(variables)

        if experiment_name:
            ret = self.run_single_experiment(experiment_name, with_hook=(not self._no_hooks))
            return ret

        return None



def make_action(auto_var, var_name):
    class CheckArgParseAction(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            argument = values
            if not auto_var.match_variable(var_name, argument):
                raise argparse.ArgumentTypeError(
                    'Argument "%s" not in Variable "%s".' % (argument, var_name))
            setattr(args, self.dest, values)
    return CheckArgParseAction
