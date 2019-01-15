def register_var(var_name: str=None, argument: str=None):
    """[summary]

    Arguments:
        func {[type]} -- [description]
        var_name {[type]} -- [description]
        argument {[type]} -- [description]
    """
    def decorator(func):
        func.register = {'var_name': var_name, 'argument': argument}
        return func
    return decorator
