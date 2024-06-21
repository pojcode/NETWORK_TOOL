import os

def check_OS():
    '''
    Return "nt" if host OS is Windows, else return "posix" -> Linux, MacOS
    '''
    return os.name

def clear_console():
    if check_OS() == 'nt':
        keyword:str = 'cls' 
    else:
        keyword:str = 'clear'
    os.system(keyword)

def load_file(filename:str, path:str=None):
    if path:
        if check_OS() == 'nt':
            sep:str = '\\'
        else:
            sep:str = '//'
        filename = f'{path}{sep}{filename}'
    with open(filename, 'r') as file_obj:
        file_content:tuple[str] = tuple(file_obj.readlines())
    
    return file_content

def save_file(filename:str, data:str, path:str=None):
    if path:
        if check_OS() == 'nt':
            sep:str = '\\'
        else:
            sep:str = '//'
        filename = f'{path}{sep}{filename}'
    with open(filename, 'w') as file_obj:
        file_obj.write(data)

def create_dir(dir_name:str, path:str=None):
    if path:
        if check_OS() == 'nt':
            sep:str = '\\'
        else:
            sep:str = '//'
        dir_name = f'{path}{sep}{dir_name}'
    os.mkdir(dir_name)