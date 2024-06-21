'''
Specific Vendor Command Handler for NETWORK_TOOL
'''
from netmiko import BaseConnection

def is_vendor_handled(device_vendor:str):
    # Add new vendors to the tuple based on names in device_type_supported_PLATFORMS.txt
    vendors:tuple[str] = (
        'cisco_ios', 'cisco_ios_telnet', 'cisco_xe', 
        'paloalto_panos', 'paloalto_panos_telnet'
    )
    matched_vendor:bool = False
    for v in vendors:
        if v == device_vendor.lower():
            matched_vendor:bool = True
            break
    
    return matched_vendor

def vendor_command_handler(
        net_connect:BaseConnection, session_mode:str, command:str, 
        command_timeout:int, output_command:str, files_to_check:tuple[str],
        fname:str, device:dict[str, str|int], send_command:bool,
        reloading:bool, error_reload:bool, precommand:bool=False
):
    vendor:str = device.get('device_type')
    # Add your vendor here using an if vendor in (xxxxx) and call created function for vendor
    if vendor in ('cisco_ios', 'cisco_ios_telnet', 'cisco_xe'):
        output_command, send_command, reloading, error_reload = (
            cisco_ios_xe_command_handler(
                net_connect=net_connect,
                session_mode=session_mode,
                command=command, 
                command_timeout=command_timeout,
                output_command=output_command, 
                files_to_check=files_to_check, 
                fname=fname,
                device=device, 
                send_command=send_command,
                reloading=reloading,
                error_reload=error_reload,
                precommand=precommand
            )
        )
    elif vendor in ('paloalto_panos', 'paloalto_panos_telnet'):
        pass
            
    return output_command, send_command, reloading, error_reload

# Create a function to handle vendor especific commands
def cisco_ios_xe_command_handler(
        net_connect:BaseConnection, session_mode:str, command:str, 
        command_timeout:int, output_command:str, files_to_check:tuple[str],
        fname:str, device:dict[str, str|int], send_command:bool,
        reloading:bool, error_reload:bool, precommand:bool=False
):
    if precommand:
        if (
            (command.lower().startswith('copy') or
             command.lower().startswith('do copy')) and 
            command.lower().endswith('flash:') and
            len(files_to_check) > 0
        ):
            if net_connect.check_config_mode():
                keyword:str = 'do dir'
            else:
                keyword:str = 'dir'
            output_dir:str = net_connect.send_command_timing(
                command_string=keyword, 
                read_timeout=10
            )
            for v in files_to_check:
                if v in output_dir and v in command:
                    file_dir:str = net_connect.send_command_timing(
                        command_string=f'{keyword} | i {v}',
                        read_timeout=10
                    )
                    file_dir:str = (
                        f'| Current device flash: | {file_dir.strip()} |'
                    )
                    file_dir:str = (
                        f'{"-"*len(file_dir)}\n'
                        f'{file_dir}\n'
                        f'{"-"*len(file_dir)}'
                    )
                    print(
                        f'{" "*2}{session_mode} {device["host"]} -> '
                        f'Performing command [{fname}{command}] |SKIPPED|, '
                        f'{v} already present in device flash'
                    )
                    output_command:str = (
                        f'SKIPPED, {v} already present in device\n{file_dir}'
                    )
                    send_command:bool = False
                    break
    else:
        if (
            command.lower().startswith('relo') or 
            command.lower().startswith('do relo')
        ):
            if 'save' in output_command.lower():
                net_connect.send_command_timing('no', read_timeout=10)
                output_command += 'no\n'
            try:   
                net_connect.send_command('\n', read_timeout=command_timeout)
            except:
                output_command += '\nReload Performed Successfully'
                reloading:bool = True
                error_reload:bool = False
            else:
                output_command += '\nReload NOT Performed Successfully'
                reloading:bool = False
                error_reload:bool = True
        elif (
            command.lower().startswith('del') or 
            command.lower().startswith('do del')
        ):
            output_command += net_connect.send_command_timing(
                command_string='\n', 
                read_timeout=command_timeout
            )
            if 'error' not in output_command.lower():
                output_command += '\nFile Deleted Successfully'
        elif (
            command.lower().startswith('wr') or
            command.lower().startswith('do wr')
        ):
            if 'era' in command.lower():  # wr erase
                output_command += '\n'
                output_command += net_connect.send_command_timing(
                    command_string="\n", 
                    read_timeout=command_timeout
                )
            else:
                if 'ok' not in output_command.lower():
                    output_command += f'[OK]'
                # Avoid weird output in next command
                net_connect.send_command_timing('\n', read_timeout=10)
        elif (
            (command.lower().startswith('inst') or 
             command.lower().startswith('do inst')) and 
             'rem' in command.lower() and 'ina' in command.lower()
        ):
            if (
                'y/n' in output_command.lower() or 
                'nothing' in output_command.lower()
            ):
                if 'y/n' in output_command.lower():
                    if output_command.count('y/n') > 1:
                        y_n_index:int = output_command.index('y/n')
                        output_command:str = output_command[:y_n_index+3]
                    output_command:str = f'{output_command.strip()}] y\n'
                    output_command += net_connect.send_command_timing(
                        command_string='y', 
                        read_timeout=command_timeout
                    )
            else:
                output_command:str = net_connect.read_until_prompt_or_pattern(
                    pattern=r'y/n', 
                    read_timeout=command_timeout
                )
                if 'y/n' in output_command.lower():
                    output_command:str = f'{output_command}] y\n'
                    net_connect.send_command_timing('y', read_timeout=10)
                    output_command += net_connect.read_until_prompt(
                        read_timeout=command_timeout
                    )
            output_command:str = output_command.replace(
                net_connect.base_prompt,
                ''
            )
            # Avoid weird output in next command
            net_connect.send_command_timing('\n', read_timeout=10)

    return output_command, send_command, reloading, error_reload