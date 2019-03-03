import unittest
import argparse

from sklearn.datasets import make_moons

from autovar import AutoVar
from autovar.base import RegisteringChoiceType, VariableClass, \
    register_var, VariableNotRegisteredError, VariableValueNotSetError

class DatasetVarClass(VariableClass, metaclass=RegisteringChoiceType):
    var_name = 'dataset'

    @register_var(argument=r"halfmoon_(?P<n_samples>\d+)")
    @staticmethod
    def halfmoon(auto_var, var_value, inter_var, n_samples):
        X, y = make_moons(
            n_samples=int(n_samples),
            noise=0.3,
            random_state=1126,
        )
        return X, y

class OrdVarClass(VariableClass, metaclass=RegisteringChoiceType):
    var_name = "ord"

    @register_var(argument='2')
    @staticmethod
    def l2(auto_var, var_value, inter_var):
        return 2

    @register_var(argument='1')
    @staticmethod
    def l1(auto_var, var_value, inter_var):
        return 1

class TestAutovar(unittest.TestCase):
    def setUp(self):
        pass

    def test_cmd_args(self):
        auto_var = AutoVar()
        self.assertFalse(auto_var._no_hooks)
        args = ['--no-hooks']
        auto_var.parse_argparse(args=args)
        self.assertTrue(auto_var._no_hooks)

    def test_cmd_args_with_vars(self):
        auto_var = AutoVar()
        auto_var.add_variable_class(DatasetVarClass())

        args = ['--dataset', 'halfmoon_300']
        auto_var.parse_argparse(args=args)

        with self.assertRaises(argparse.ArgumentTypeError):
            args = ['--dataset', 'halfmaan_300']
            auto_var.parse_argparse(args=args)

    def test_val(self):
        auto_var = AutoVar()
        with self.assertRaises(VariableNotRegisteredError):
            auto_var.get_var('ord')

        auto_var.add_variable_class(OrdVarClass())
        auto_var.add_variable_class(DatasetVarClass())
        auto_var.add_variable('random_seed', int)

        with self.assertRaises(VariableValueNotSetError):
            auto_var.get_var('ord')

        auto_var.set_variable_value_by_dict({
            'ord': '1', 'dataset': 'halfmoon_200', 'random_seed': 1126
        })

        self.assertEqual(auto_var.get_var('ord'), 1)
        self.assertEqual(auto_var.get_var('random_seed'), 1126)
        self.assertEqual(len(auto_var.get_var('dataset')[0]), 200) 
        self.assertEqual(
            len(auto_var.get_var_with_argument('dataset', 'halfmoon_300')[0]), 300) 

        with self.assertRaises(ValueError):
            auto_var.set_variable_value_by_dict({'ord': 'l2'})

        with self.assertRaises(TypeError):
            auto_var.set_variable_value_by_dict({'random_seed': '1126.0'})



if __name__ == '__main__':
    unittest.main()