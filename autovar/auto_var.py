from copy import deepcopy
from typing import Dict, Tuple, List, Any, Callable, AnyStr
import pprint
import base64
import logging
import argparse

import git
from sklearn.model_selection import ParameterGrid
from mkdir_p import mkdir_p
from flask_restful import reqparse

from .base import variables, default_fn_dict, default_val_dict, \
        ParameterAlreadyRanError

logger = logging.getLogger(__name__)


class AutoVar(object):

    def __init__(self, before_experiment_hooks=None, after_experiment_hooks=None,
                 settings: Dict = None):
        """
        settings : {
            'server_url': 'http://127.0.0.1:8080/nn_attack/',
            'result_file_dir': './results/'
        }
        """
        self.variables: Dict[str, dict] = variables
        self.var_class: Dict[str, Any] = {}
        self.var_value: Dict[str, Any] = {}
        self.inter_var: Dict[str, Any] = {}
        self.result_fields: List[str] = []
        self.settings: Dict = settings
        if 'result_file_dir' in self.settings and self.settings['result_file_dir']:
            mkdir_p(self.settings['result_file_dir'])

        repo = git.Repo(search_parent_directories=True)
        self.var_value['git_hash'] = repo.head.object.hexsha

        self.after_experiment_hooks = after_experiment_hooks
        self.before_experiment_hooks = before_experiment_hooks

        self._read_only: bool = False

    def add_variable_class(self, variable_class, var_name: str = None):
        if var_name is None:
            var_name = variable_class.__class__.var_name
            if var_name is None:
                var_name = type(variable_class).__name__

        if var_name in self.var_class:
            raise ValueError('Don\'t register class "{}" twice '.format(var_name))
        self.var_class[var_name] = variable_class
        self.variables.setdefault(var_name, deepcopy(default_fn_dict))

    def add_variable(self, var_name: str, dtype) -> None:
        d = deepcopy(default_val_dict)
        d['dtype'] = dtype
        self.variables.setdefault(var_name, d)

    def get_variable_value(self, var_name: str):
        if var_name not in self.var_value:
            raise ValueError(f"{var_name} not in var_value")
        return self.var_value[var_name]

    def set_variable_value(self, var_name: str, value) -> None:
        if self._read_only:
            raise ValueError("should not set variable value while read_only")
        if var_name not in self.var_value:
            pass
        self.var_value[var_name] = value

    def set_intermidiate_variable(self, var_name: str, value) -> None:
        self.inter_var[var_name] = value

    def get_intermidiate_variable(self, var_name: str):
        return self.inter_var[var_name]

    def set_variable_value_by_dict(self, var_value: Dict[str, Any]) -> None:
        if self._read_only:
            raise ValueError("should not set variable value while read_only")
        for k, v in var_value.items():
            self.set_variable_value(k, v)

    def _run_before_hooks(self):
        if self.before_experiment_hooks is not None:
            for hook_fn in self.before_experiment_hooks:
                try:
                    hook_fn(self)
                except ParameterAlreadyRanError:
                    logger.warning("The result for this parameter is already ran.")
                    return False
                except:
                    print("Error occur during running before hooks.")
                    raise
        return True

    def _run_after_hooks(self, ret):
        if self.after_experiment_hooks is not None:
            for hook_fn in self.after_experiment_hooks:
                hook_fn(self, ret)

    def get_var_with_argument(self, var_name: str, argument: str, *args, **kwargs):
        if self.variables[var_name]["type"] == "val":
            return argument
        else:
            if argument not in self.variables[var_name]["argument_fn"]:
                raise ValueError('Argument "%s" not in Variable "%s".' % (argument, var_name))
            func = self.variables[var_name]["argument_fn"][argument]
            kwargs['auto_var'] = self
            kwargs['var_value'] = self.var_value
            kwargs['inter_var'] = self.inter_var
            return func(*args, **kwargs)

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
            raise ValueError('Variable "%s" not registered.' % var_name)
        if var_name not in self.var_value:
            raise ValueError('Value for variable "%s" is not assigned.' % var_name)
        argument = self.var_value[var_name]

        if self.variables[var_name]["type"] == "val":
            return argument
        else:
            if argument not in self.variables[var_name]["argument_fn"]:
                raise ValueError('Argument "%s" not in Variable "%s".' % (argument, var_name))
            func = self.variables[var_name]["argument_fn"][argument]
            kwargs['auto_var'] = self
            kwargs['var_value'] = self.var_value
            kwargs['inter_var'] = self.inter_var
            return func(*args, **kwargs)

    def run_single_experiment(self, experiment_fn: Callable[..., Any],
                              with_hook: bool=True) -> bool:
        self._read_only = True
        logger.info("running: %s", str(self.var_value))

        try:
            if with_hook:
                ret = self._run_before_hooks()
            else:
                ret = True
            if ret:
                ret = experiment_fn(self)
                if with_hook:
                    self._run_after_hooks(ret)
        finally:
            self.inter_var.clear()
            self._read_only = False
        return ret

    def run_grid_params(self, experiment_fn: Callable[..., Any],
                        grid_params: Dict[AnyStr, List],
                        with_hook: bool=True,
                        max_params: int=-1, 
                        verbose: int=0) -> (Dict, Dict):
        ret_params = []
        ret_results = []
        grid = ParameterGrid(grid_params)
        prev_state = deepcopy(self.var_value)
        i = 0
        for params in grid:
            self.set_variable_value_by_dict(params)
            if verbose:
                logger.info("Running parameter:" + str(params))

            ret_params.append(params)
            ret_results.append(self.run_single_experiment(experiment_fn,
                                                          with_hook=with_hook))
            if ret_results[-1] is not False:
                i += 1
            if max_params > 0 and i >= max_params:
                break
        self.set_variable_value_by_dict(prev_state)
        return ret_params, ret_results

    def summary(self) -> None:
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.variables)

    def generate_name(self) -> str:
        _ = hash(tuple(sorted(self.var_value.items())))
        return base64.b64encode(str(_).encode()).decode()

    def parse_argparse(self):
        parser = argparse.ArgumentParser()
        for k, v in self.variables.items():
            if v['type'] == 'choice':
                parser.add_argument(f'--{k}', type=str, required=True,
                    choices=[kk for kk, _ in v['argument_fn'].items()])
            else:
                parser.add_argument(f'--{k}', type=v['dtype'], required=True)
        args = parser.parse_args()
        self.set_variable_value_by_dict(vars(args))
    
    def get_reqparse_parser(self):
        parser = reqparse.RequestParser()
        for k, v in self.variables.items():
            if v['type'] == 'choice':
                parser.add_argument(f'{k}', type=str, required=True,
                    choices=[kk for kk, _ in v['argument_fn'].items()])
            else:
                parser.add_argument(f'{k}', type=v['dtype'], required=True)
        return parser

    def generate_django_models_py(self):
        output = """
from django.db import models
"""
        for k, v in self.variables.items():
            if v['type'] is "choice":
                choices = [kk for kk, _, in v['argument_fn'].items()]
                output += "%s = %s\n" % (k.upper(), str(choices))

        output += """\n
class VariableModel(models.Model):
    git_hash = models.CharField(max_length=100)
    create_time = models.DateField(auto_now_add=True)
"""
        for k, v in self.variables.items():
            if v['type'] is "choice":
                #output += "    " * 1 + "%s = models.CharField(max_length=100)\n" % k
                output += "    " * 1 + "%s = models.ChoiceField(max_length=100)\n" % k
            elif v['type'] is "val":
                if v['dtype'] is int:
                    output += "    " * 1 + "%s = models.IntegerField()\n" % k
                elif v['dtype'] is float:
                    output += "    " * 1 + "%s = models.FloatField()\n" % k
                else:
                    output += "    " * 1 + "%s = models.CharField(max_length=100)\n" % k

        output += """\n
class ResultFileModel(models.Model):
    file_field = models.FileField()
    create_time = models.DateField(auto_now_add=True)
    variable = models.ForeignKey(
        'VariableModel',
        on_delete=models.CASCADE,
    )
"""
        print(output)

    def generate_django_serializers_py(self):
        output = """
from rest_framework import serializers

from .models import VariableModel


class VariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariableModel
        fields = %s
"""
        fields = ['id', 'unique_name', 'create_time']
        fields += [k for k in self.variables.keys()]

        output = output % str(tuple(fields))

        output += """\n
class ResultFileModel(serializers.ModelSerializer):
    class Meta:
        model = VariableModel
        fields = ('file_field', 'variable')
"""
        print(output)
