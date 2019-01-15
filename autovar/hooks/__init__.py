import os
import urllib.parse
import tempfile
import json
import copy
from typing import Dict, Tuple, List, Any, Callable, AnyStr
import logging

import requests
from mkdir_p import mkdir_p

from ..base import ParameterAlreadyRanError

_logger = logging.getLogger(__name__)

def check_result_file_exist(auto_var, get_name_fn=None):
    if get_name_fn is None:
        get_name_fn = lambda x: x.generate_name()
    unique_name = get_name_fn(auto_var)
    unique_name = f'{unique_name}.json'
    if os.path.exists(unique_name):
        raise ParameterAlreadyRanError("%s exists" % unique_name)

def save_result_to_file(auto_var, ret, get_name_fn=None):
    if get_name_fn is None:
        get_name_fn = lambda x: x.generate_name()

    unique_name = get_name_fn(auto_var)
    output_file = '%s.json' % unique_name
    with open(output_file, "w") as f:
        json.dump(ret, f)
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
