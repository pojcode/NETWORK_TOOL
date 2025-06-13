'''
OS/system related functions
'''

import os


def check_OS():
    '''
    Return "nt" if host OS is Windows, else return "posix" if Linux, MacOS
    '''
    return os.name

def get_OS_path_separator():
    if check_OS() == 'nt':  # Windows
        sep:str = '\\'
    else:  # Linux, MacOS
        sep:str = '//'
    
    return sep

def clear_console():
    if check_OS() == 'nt':  # Windows
        keyword:str = 'cls' 
    else:  # Linux, MacOS
        keyword:str = 'clear'
    os.system(keyword)

def load_file(filename:str, path:str|None=None, mode:str='r'):
    if path:
        sep:str = get_OS_path_separator()
        filename:str = f'{path}{sep}{filename}'
    with open(filename, mode) as file_obj:
        file_content:tuple[str] = tuple(file_obj.readlines())
    
    return file_content

def save_file(filename:str, data:str, path:str|None=None, mode:str='w'):
    if path:
        sep:str = get_OS_path_separator()
        filename:str = f'{path}{sep}{filename}'
    with open(filename, mode) as file_obj:
        file_obj.write(data)

def create_dir(dir_name:str, path:str|None=None):
    if path:
        sep:str = get_OS_path_separator()
        dir_name:str = f'{path}{sep}{dir_name}'
    os.mkdir(dir_name)