import ipaddress, subprocess

def validate_ip(ip:str):
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    else:
	    return True

def create_ip_range(ip_start:str, ip_end:str, step:int=1):
    ip_list:list[str] = []
    for ip in range(
        int(ipaddress.ip_address(ip_start)), 
        int(ipaddress.ip_address(ip_end))+1, 
        step
    ):
        ip_list.append(str(ipaddress.ip_address(ip)))

    return tuple(ip_list)

def sort_ip(ip_values:list[str]|tuple[str]|set[str], reverse=False):
    sorted_ip_list:list[str] = []
    int_ip_list:list[int] = []
    for v in ip_values:
        int_ip_list.append(int(ipaddress.ip_address(v)))
    int_ip_list:list[int] = sorted(int_ip_list, reverse=reverse)
    for v in int_ip_list:
        sorted_ip_list.append(str(ipaddress.ip_address(v)))

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