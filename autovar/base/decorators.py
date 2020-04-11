from typing import List, Optional
import joblib
import logging

_logger = logging.getLogger(__name__)

def register_var(var_type: str = 'fn_name', var_name: str = None,
                 argument: str = None, shown_name: str = None):
    """[summary]

    Arguments:
        func {[type]} -- [description]
        var_name {[type]} -- [description]
        argument {[type]} -- [description]
    """
    def decorator(func):
        data = {
            'var_type': var_type,
            'var_name': var_name,
            'argument': argument,
            'shown_name': shown_name,
        }
        if hasattr(func, 'registers'):
            func.registers.append(data)
        else:
            func.registers = [data]
        return func
    return decorator

def requires(required_vars: List[str]):
    """
    Should com after register_var decorator.
    """
    def decorator(func):
        if hasattr(func, 'registers'):
            for reg in func.registers:
                reg['required_vars'] = required_vars
        return func
    return decorator

def cache_outputs(cache_dir: str):
    """
    Should com after register_var decorator.
    """
    def decorator(func):
        if hasattr(func, 'registers'):
            for reg in func.registers:
                reg['cache_dir'] = cache_dir
        return func
    return decorator
