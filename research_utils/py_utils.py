'''
	Useful functions in python
'''
#### Standard Library Imports

#### Library imports

#### Local imports
from research_utils.shared_constants import EPSILON


def get_obj_functions(obj, filter_str: str = ''):
    '''
        Get all callable functions of the object as a list of strings.
        filter_str only appends the functions that contain the filter_str 
    '''
    obj_funcs = []
    for func_name in dir(obj):
        if((callable(getattr(obj, func_name))) and (filter_str in func_name)):
            obj_funcs.append(func_name)
    return obj_funcs

def tuple2str(tup, separator: str = '') -> str: 
    return separator.join(map(str,tup))

def is_float_equal(f1: float, f2: float) -> bool:
    return abs(f1-f2) <= EPSILON