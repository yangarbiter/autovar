def register_var(var_type: str = 'fn_name', var_name: str = None,
                 argument: str = None, shown_name: str = None):
    """[summary]

    Arguments:
        func {[type]} -- [description]
        var_name {[type]} -- [description]
        argument {[type]} -- [description]
    """
    def decorator(func):
        func.register = {
            'var_type': var_type,
            'var_name': var_name,
            'argument': argument,
            'shown_name': shown_name,
        }
        return func
    return decorator

def require():
    # TODO
    pass
