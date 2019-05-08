import unittest
import argparse

from numpy.testing import assert_array_equal
from sklearn.datasets import make_moons

from autovar import AutoVar
from autovar.base import RegisteringChoiceType, VariableClass, \
    register_var, VariableNotRegisteredError, VariableValueNotSetError

class DatasetVarClass(VariableClass, metaclass=RegisteringChoiceType):
    """Dataset variable class"""
    var_name = 'dataset'

    @register_var(argument=r"moon_(?P<n_samples>\d+)", shown_name="shown_halfmoon")
    @register_var(argument=r"halfmoon_(?P<n_samples>\d+)", shown_name="shown_halfmoon")
    @staticmethod
    def halfmoon(auto_var, var_value, n_samples):
        """halfmoon dataset"""
        X, y = make_moons(
            n_samples=int(n_samples),
            noise=0.3,
            random_state=1126,
        )
        return X, y

    @register_var(argument=r"no2_halfmoon_(?P<n_samples>\d+)", shown_name="no2_halfmoon")
    @staticmethod
    def no2_halfmoon(auto_var, var_value, n_samples):
        """no2 halfmoon dataset"""
        X, y = make_moons(
            n_samples=int(n_samples),
            noise=0.2,
            random_state=1126,
        )
        return X, y

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

        self.assertEqual(
            auto_var.get_var_shown_name(var_name="dataset"),
            'shown_halfmoon')

        assert_array_equal(
            auto_var.get_var_with_argument('dataset', 'halfmoon_300')[0],
            auto_var.get_var_with_argument('dataset', 'moon_300')[0],
        )
        argparse_help = auto_var.get_argparser().format_help()
        self.assertTrue('halfmoon dataset' in argparse_help)
        self.assertTrue('Dataset variable class' in argparse_help)

    def test_run_grid(self):
        auto_var = AutoVar()
        auto_var.add_variable_class(OrdVarClass())
        auto_var.add_variable_class(DatasetVarClass())
        auto_var.add_variable('random_seed', int)

        grid_params = {
            "ord": ['1', '2'],
            "dataset": ['halfmoon_50', 'halfmoon_10'],
            "random_seed": [1126],
        }
        def fn(auto_var):
            return auto_var.var_value
        params, results = auto_var.run_grid_params(
                fn, grid_params=grid_params, n_jobs=1)

        del results[0]['git_hash']
        del results[0]['running_time']
        self.assertEqual(
            params[0],
            {'ord': '1', 'dataset': 'halfmoon_50', 'random_seed': 1126})
        self.assertEqual(params[0], results[0])


if __name__ == '__main__':
    unittest.main()
