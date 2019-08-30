from functools import partial
import json
import os
import unittest
import shutil

import joblib
from numpy.testing import assert_array_equal
from mkdir_p import mkdir_p

from autovar import AutoVar
from autovar.base import RegisteringChoiceType, VariableClass, \
    register_var, VariableNotRegisteredError, VariableValueNotSetError
from autovar.hooks import save_result_to_file, default_get_file_name

class OrdVarClass(VariableClass, metaclass=RegisteringChoiceType):
    var_name = "ord"

    @register_var(argument='2')
    @staticmethod
    def l2(auto_var):
        return 2

    @register_var(argument='1')
    @staticmethod
    def l1(auto_var, var_value, inter_var):
        return 1

class TestAutovar(unittest.TestCase):
    def setUp(self):
        pass

    def test_json_file(self):
        settings = {'file_format': 'json', 'result_file_dir': 'test'}
        mkdir_p(settings['result_file_dir'])
        auto_var = AutoVar(
            settings=settings,
            after_experiment_hooks=[
                partial(save_result_to_file, get_name_fn=default_get_file_name)
            ],
        )
        auto_var.add_variable_class(OrdVarClass())
        auto_var.set_variable_value_by_dict({'ord': '1'})

        def experiment(auto_var):
            return {'test': auto_var.get_var('ord')}

        _ = auto_var.run_single_experiment(experiment, with_hook=True)

        with open("test/1.json", 'r') as f:
            ret = json.load(f)
        self.assertEqual(ret['test'], auto_var.get_var('ord'))
        shutil.rmtree(settings['result_file_dir'])



if __name__ == '__main__':
    unittest.main()
