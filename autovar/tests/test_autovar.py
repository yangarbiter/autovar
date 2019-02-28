import unittest

from autovar import AutoVar
from autovar.base import RegisteringChoiceType, VariableClass, register_var


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

if __name__ == '__main__':
    unittest.main()