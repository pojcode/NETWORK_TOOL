'''
Network related functions
'''

import ipaddress, subprocess


def validate_ip(ip:str):
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    else:
	    return True

def convert_ip_to_integer(ip:str):
    int_ip:int = int(ipaddress.ip_address(ip))

    return int_ip

def convert_integer_to_ip(int_ip:int):
    ip:str = str(ipaddress.ip_address(int_ip))

    return ip

def create_ip_range(ip_start:str, ip_end:str, step:int=1):
    ip_list:list[str] = []
    range_start:int = convert_ip_to_integer(ip_start)
    range_end:int = convert_ip_to_integer(ip_end)
    for int_ip in range(range_start, range_end + 1, step):
        ip_list.append(convert_integer_to_ip(int_ip))

    return tuple(ip_list)

def sort_ip(ip_values:list[str]|tuple[str]|set[str], reverse=False):
    int_ip_list:list[int] = []
    for ip in ip_values:
        int_ip_list.append(convert_ip_to_integer(ip))
    int_ip_list:list[int] = sorted(int_ip_list, reverse=reverse)
    sorted_ip_list:list[str] = []
    for int_ip in int_ip_list:
        sorted_ip_list.append(convert_integer_to_ip(int_ip))

    return tuple(sorted_ip_list)

def ping(
        ip:str, t:bool=False, n:int=4, l:int=32, w:int=4000,
        capture_output=False
):
    if t:
        ping_obj:subprocess.CompletedProcess[str] = (
            subprocess.run(
                args=f'ping {ip} -t -w {w} -l {l}', 
                capture_output=capture_output, 
                text=True
            )
        )
    else:
        ping_obj:subprocess.CompletedProcess[str] = (
            subprocess.run(
                args=f'ping {ip} -n {n} -w {w} -l {l}',
                capture_output=capture_output, 
                text=True
            )
        )

    return ping_obj