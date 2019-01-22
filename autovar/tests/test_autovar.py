import unittest

from autovar import AutoVar

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