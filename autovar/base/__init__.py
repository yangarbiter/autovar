"""
"""
from typing import Dict
from copy import deepcopy
from .decorators import register_var

default_fn_dict = {
    "type": "choice",
    "argument_fn": {},
    "default": None,
}
default_val_dict = {
    "type": "val",
    "dtype": None,
    "default": None,
}

class VariableClass(object):
    var_name: str = ""

class RegisteringChoiceType(type):
    def __init__(cls, name, bases, attrs):
        cls.arguments = []
        cls.variables: Dict[str, dict] = {}
        if hasattr(cls, 'var_name') and cls.var_name is not None:
            name = cls.var_name
        elif not hasattr(cls, 'var_name'):
            # shouldn't happend
            cls.var_name = name

        for key, val in attrs.items():
            prop = getattr(val, 'register', None)
            if prop is not None:
                var_name = name if not prop['var_name'] else prop['var_name']
                argument = key if not prop['argument'] else prop['argument']
                #variables.setdefault(var_name, deepcopy(default_fn_dict))["argument_fn"][argument] = val.__func__
                cls.variables.setdefault(var_name, deepcopy(default_fn_dict))["argument_fn"][argument] = val.__func__
                cls.arguments.append(argument)

class ParameterAlreadyRanError(Exception):
    def __init__(self, message="", errors=""):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors

class VariableValueNotSetError(Exception):
    def __init__(self, message="", errors=""):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors

class VariableNotRegisteredError(Exception):
    def __init__(self, message="", errors=""):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors
