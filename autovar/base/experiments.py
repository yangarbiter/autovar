from typing import Any, Callable, Dict, List, Optional, Union
from ..auto_var import AutoVar

class Experiments():
    name: str
    experiment_fn: Callable[[AutoVar], Any]
    grid_params: Union[List[Dict[str, str]], Dict[str, str]]
    run_param: Dict[str, Any]

    def __init__(self):
        pass

    def __call__(self):
        return self.experiment_fn, self.name, self.grid_params, self.run_param
