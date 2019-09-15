import os
import urllib.parse
import tempfile
import json
import copy
from typing import Dict, Tuple, List, Any, Callable, AnyStr
import logging

import requests
from mkdir_p import mkdir_p
import joblib

from ..base import ParameterAlreadyRanError
from ..auto_var import AutoVar

_logger = logging.getLogger(__name__)

def get_ext(file_format: str) -> str:
    if file_format == 'json':
        return 'json'
    elif file_format == 'pickle': 
        return 'pkl'
    else:
        raise ValueError(f"Not supported file format {file_format}")

def default_get_file_name(auto_var: AutoVar) -> str:
    file_name_list: List[str] = []
    for k, v in sorted(auto_var.var_value.items()):
        if k != 'git_hash':
            file_name_list.append(f"{str(v)}")
    file_name: str = '-'.join(file_name_list)
    return file_name

def check_result_file_exist(auto_var, get_name_fn=None):
    if get_name_fn is None:
        get_name_fn = lambda x: x.generate_name()
    unique_name = get_name_fn(auto_var)
    unique_name = f'{unique_name}.{get_ext(auto_var.settings["file_format"])}'
    base_dir = auto_var.settings['result_file_dir']
    file_path = os.path.join(base_dir, unique_name)
    if os.path.exists(file_path):
        _logger.warning(f"{file_path} exists")
        raise ParameterAlreadyRanError("%s exists" % file_path)

def save_result_to_file(auto_var, ret, get_name_fn=None):
    if get_name_fn is None:
        get_name_fn = lambda x: x.generate_name()

    base_dir = auto_var.settings['result_file_dir']
    file_format = auto_var.settings["file_format"]
    unique_name = get_name_fn(auto_var)
    output_file = os.path.join(base_dir, f'{unique_name}.{get_ext(file_format)}')
    if file_format == 'json':
        with open(output_file, "w") as f:
            json.dump(ret, f)
    elif file_format == 'pickle':
        with open(output_file, "wb") as f:
            joblib.dump(ret, f)
    else:
        raise ValueError(f"Not supported file format {file_format}")
    _logger.info("Finish writing to file %s", output_file)

def save_parameter_to_file(auto_var, get_name_fn=None):
    if get_name_fn is None:
        get_name_fn = lambda x: x.generate_name()

    unique_name = get_name_fn(auto_var) + "_param"
    output_file = '%s.json' % unique_name
    with open(output_file, "w") as f:
        json.dump(auto_var.var_value, f)
    _logger.info("Finish writing to file %s", output_file)

def upload_result(auto_var, ret):
    #files = {'file_field': json.dumps(ret)}
    if auto_var.parameter_id is None:
        raise ValueError
    url = urllib.parse.urljoin(auto_var.settings['server_url'], 'upload_result')
    payload = {}
    payload['variable'] = auto_var.parameter_id

    fp = tempfile.NamedTemporaryFile('w', delete=False)
    json.dump(ret, fp)
    fp.close()
    files = {'file_field': open(fp.name, 'r')}

    res = requests.post(url, data=payload, files=files)
    print(res.content)

def submit_parameter(auto_var):
    if auto_var.settings['server_url'] is None:
        raise ValueError
    url = urllib.parse.urljoin(auto_var.settings['server_url'], 'submit_parameter')
    payload = copy.deepcopy(auto_var.var_value)
    #payload['unique_name'] = auto_var.generate_name()
    res = requests.post(url, data=json.dumps(payload))
    response_content = json.loads(res.content)
    if response_content['has_result']:
        raise ParameterAlreadyRanError
    auto_var.parameter_id = response_content['id']
    return res
