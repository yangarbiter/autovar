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

def require():
    # TODO
    pass
