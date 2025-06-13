'''
NETWORK_TOOL -- App Functions
'''

import time
from threading import Lock
from subprocess import CompletedProcess
from netmiko import ConnectHandler, SSHDetect, BaseConnection
from app.system import load_file
from app.vendor import is_vendor_handled, vendor_command_handler
from app.network import validate_ip, ping, convert_ip_to_integer
from app.utils import colorize, text_to_box
from app.templates import get_default_data_file_values, get_default_cfg_values


def create_db(raw_data_file:tuple[str]):
    main_DB:dict[str, str|tuple[str|int]|dict[int, str|int]] = {}
    is_command:bool = False
    command_list:list[str] = []
    for line in raw_data_file:
        line_upper:str = line.upper()
        if (
            line_upper.startswith('-USERNAME:') or 
            line_upper.startswith('-PASSWORD:') or
            line_upper.startswith('-ENABLE_PASSWORD:') or
            line_upper.startswith('-HOST:') or
            line_upper.startswith('-PING:') or 
            line_upper.startswith('-SSH_TELNET:') or
            line_upper.startswith('-FILES:')
        ):
            line = line.strip().split(':', maxsplit=1)
            main_DB[line[0][1:].strip().upper()] = line[1].strip()
            if (
                line_upper.startswith('-HOST:') or
                line_upper.startswith('-FILES:')
            ):
                values_list:list[str] = [] 
                if line_upper.startswith('-HOST:'):
                    keyword:str = 'HOST'
                else:
                    keyword = 'FILES'
                entry:str = main_DB.get(keyword)
                if ',' in entry:
                    for v in entry.split(','):
                        if len(v.strip()) > 0:
                            values_list.append(v.strip())
                else:
                    if len(entry) > 0:
                        values_list.append(entry)
                main_DB[keyword] = tuple(values_list)
        elif line_upper.startswith('-COMMANDS:'):
            is_command:bool = True
        elif is_command:
            if len(line.strip()) > 0:
                command_list.append(line.strip())
    main_DB['COMMANDS'] = tuple(command_list)

    return main_DB

def create_data_table(values:dict[str, str|tuple[str]], title:str):
    max_lenght:int = 0
    data_list:list[str] = []
    if len(title) > max_lenght:
        max_lenght:int = len(title)
    for k, v in values.items():
        if type(v) == tuple:
            data:str = f'-{k}: {", ".join(v)}'
            if len(data) > 100:
                format_data:str = ''
                for i, v in enumerate(data):
                    format_data += v
                    if v == ',' and len(format_data) >= 100:
                        if len(format_data) > max_lenght:
                            max_lenght:int = len(format_data)
                        data_list.append(format_data)
                        format_data:str = " "*len(f'-{k}:')
                    elif i == (len(data)-1):  # last iteration
                        if len(format_data) > max_lenght:
                            max_lenght:int = len(format_data)
                        data_list.append(format_data)
            else:
                if len(data) > max_lenght:
                    max_lenght:int = len(data)
                data_list.append(data)
        else:
            data:str = f'-{k}: {v}'
            if len(data) > max_lenght:
                max_lenght:int = len(data)
            data_list.append(data)
    table:str = (
        f'{"-"*(max_lenght + 4)}\n'
        f'| {title.ljust(max_lenght)} |\n'
        f'{"-"*(max_lenght + 4)}'
    )
    for v in data_list:
        table += f'\n| {v.ljust(max_lenght)} |'
    table += f'\n{"-"*(max_lenght + 4)}'

    return table

def validate_db(main_DB:dict[str, str|tuple[str|int]|dict[int, str|int]]):
    default_entries:tuple[str] = get_default_data_file_values()
    error:list[str] = []
    if len(main_DB.keys()) != len(default_entries):
        for v in default_entries:
            if v not in main_DB.keys():
                error.append(
                    f'-{v}: Entry not found, check entry "-{v}:" is '
                    'present in data_file'
                )
                if v in ('HOST', 'FILES', 'COMMANDS'):
                    main_DB[v] = ()
                else:
                    main_DB[v] = ''
    else:
        if len(main_DB.get('HOST')) > 0:
            if main_DB.get('SSH_TELNET').lower() in ('y', 'ye', 'yes'):
                mandatory_entries:tuple[str] = (
                    'USERNAME', 'PASSWORD', 'HOST', 'PING', 'SSH_TELNET'
                )
            elif main_DB.get('PING').lower() in ('y', 'ye', 'yes'):
                mandatory_entries:tuple[str] = ('HOST', 'PING', 'SSH_TELNET')
            else:
                error.append(
                    'At least "-PING:" or "-SSH_TELNET:" entry value must '
                    'be set to "y" to perform any action'
                )
                mandatory_entries:tuple[str] = ('PING', 'SSH_TELNET')
        else:
            error.append(
                'Entry value "-HOST:" must be filled in to perform any '
                'action (Ping, SSH/Telnet or both)'
            )
            mandatory_entries:tuple[str] = ('PING', 'SSH_TELNET')
        for k, v in main_DB.items():
            if k in mandatory_entries:
                if len(v) == 0:
                    error.append(f'-{k}: Entry value cannot be empty')
                elif k in ('PING', 'SSH_TELNET'):
                    if v.lower() not in ('y', 'ye', 'yes', 'n', 'no'):
                        error.append(
                            f'-{k}: {v} -> Entry value must be "y" or "n"'
                        )

    return tuple(error), main_DB

def validate_db_host_info(value:str):
    raw_value:str = value
    error:list[str] = []
    ip_data:list[str] = []
    step:str = ''
    do_ip_validation:bool = True
    if '<step=' in value.lower():
        n:int = 1
        step_index:int = value.lower().index('<step=')
        for v in value[step_index+6:]:
            if v != '>':
                step += v
            else:
                break
        if '-' in value.lower():  # IP range
            if value.lower().count('<step=') > 1:
                error.append(
                    f'-HOST: "{raw_value}" -> Only one step property '
                    'per IP range is allowed'
                )
                do_ip_validation:bool = False
            elif '>' not in value[step_index:]:
                error.append(
                    f'-HOST: "{raw_value}" -> Closing ">" for step '
                    'property not found'
                )
                n:int = 0
            elif step.strip().isdigit() == False or int(step.strip()) == 0:
                error.append(
                    f'-HOST: "{raw_value}" -> "<step={step}>", value '
                    'must be an integer higher than "0"'
                )
        else:  # Unique IP
            error.append(
                f'-HOST: "{raw_value}" -> Unique IP cannot contain '
                '"step" property'
            )
            if '>' not in value[step_index:]:
                n:int = 0
        if do_ip_validation:
            value:str = (
                f'{value[:step_index]}{value[step_index+6+len(step)+n:]}'
            )
            value:str = value.strip()
    if do_ip_validation:
        if '-' in value.lower():  # IP range
            if value.count('-') > 1:
                value:str = value.replace('-', '', value.count('-')-1).strip()
            for v in value.split('-', maxsplit=1):
                if v.strip():
                    is_valid_ip:bool = validate_ip(v.strip())
                    if is_valid_ip:
                        ip_data.append(v.strip())
                    else:
                        error.append(
                            f'-HOST: "{raw_value}" -> "{v.strip()}" '
                            'is not a valid IP'
                        )
            if step:
                ip_data.append(step.strip())
            else:
                ip_data.append('1')
            if len(ip_data) == 3:  # (ip_start, ip_end, step)
                int_ip_start:int = convert_ip_to_integer(ip_data[0])
                int_ip_end:int = convert_ip_to_integer(ip_data[1])
                if int_ip_start >= int_ip_end:
                    error.append(
                        f'-HOST: "{raw_value}" -> '
                        f'Range IP_start "{ip_data[0]}" '
                        f'must be lower than range IP_end "{ip_data[1]}"'
                    )
            else:
                error.append(
                    f'-HOST: "{raw_value}" -> It is not a valid IP '
                    'range (2 valid IP required, IP_start < IP_end)'
                )
        else:  # Unique IP
            is_valid_ip:bool = validate_ip(value)
            if is_valid_ip:
                ip_data.append(value)
            else:
                error.append(f'-HOST: "{value}" is not a valid IP')
            
    return tuple(error), tuple(ip_data)

def import_config_file(value:str, path:str):
    error:list[str] = []
    data_dict:dict[str, tuple[str]] = {}
    c_f_total:int = value.lower().count('<import=')
    if value.startswith('<') == False or value.endswith('>') == False:
        error.append(
            f'-COMMANDS: "{value}" -> Invalid syntax, you must only type '
            '<import=filename.extension>'
        )
    elif value.lower().count('>') < c_f_total:
        char_count:int = value.lower().count('>')
        error.append(
            f'-COMMANDS: "{value}" -> {c_f_total-char_count} closing ">" '
            f'for "{value}" missed'
        )
    elif value.lower().count('>') > c_f_total:
        char_count:int = value.lower().count('>')
        error.append(
            f'-COMMANDS: "{value}" -> {char_count-c_f_total} unnecessary '
            f'closing ">" for "{value}" found'
        )
    else:
        commands_in_file:list[str] = []
        filename:str = ''
        pos:int = 0
        for i in range(c_f_total):
            f_index:int = value.lower().index('<import=', pos)
            for z in value[f_index+8:]:
                if z != '>':
                    filename += z
                else:
                    break
            filename:str = filename.strip()
            try:
                content:tuple[str] = load_file(filename, path)
            except FileNotFoundError:
                error.append(
                    f'-COMMANDS: "{value}" -> File [{filename}] '
                    'not found in config_files directory'
                )
            else:
                for z in content:
                    if z.strip() and z.strip().startswith('#') == False:
                        commands_in_file.append(z.strip())
                data_dict[filename] = tuple(commands_in_file)
            filename:str = ''
            commands_in_file:list[str] = []
            pos:int = f_index + 1
    
    return tuple(error), data_dict

def get_command_timeout(command:str, fname:str):
    error:list[str] = []
    command_timeout:int = 10
    if command.lower().count('<timeout=') > 1:
        error.append(
            f'-COMMANDS: "{fname}{command}" -> Only one timeout property '
            'per command is allowed'
        )
    elif '>' not in command[command.lower().index('<timeout='):]:
        error.append(
            f'-COMMANDS: "{fname}{command}" -> Closing ">" for timeout '
            'property not found'
        )
    else:    
        t_index:int = command.lower().index('<timeout=')
        t_value:str = ''
        for v in command[t_index+9:]:
            if v != '>':
                t_value += v
            else:
                break
        if t_value.strip().isdigit() and int(t_value.strip()) > 0:
            command_timeout:int = int(t_value.strip())
        else:
            error.append(
                f'-COMMANDS: "{fname}{command}" -> "<timeout={t_value}>", '
                'value must be an integer higher than "0"'
            )
        alt_command:str = command.lower().replace(
            f'<timeout={t_value.lower()}>', 
            ''
        )
        if len(alt_command.strip()) == 0:
            error.append(
                f'-COMMANDS: "{fname}{command}" -> "<timeout={t_value}>", '
                'timeout property must be attached to a command'
            )
        else:
            command:str = (
                f'{command[:t_index]}{command[t_index+9+len(t_value)+1:]}'
            )
    command_data:tuple[str, int] = (command.strip(), command_timeout)

    return tuple(error), command_data

def create_cfg(values:tuple[str]):
    default_cfg_config:dict[str, str|int] = get_default_cfg_values()
    cfg_config:dict[str, str] = {}
    for v in values:
        v:str = v.strip().lower()
        for k in default_cfg_config.keys():
            if v.startswith(f'{k}='):
                v_splited:list[str] = v.split('=', maxsplit=1)
                cfg_config[v_splited[0].strip()] = v_splited[1].strip()
                break

    return cfg_config

def validate_cfg(cfg_config:dict[str, str]):
    default_cfg_config:dict[str, str|int] = get_default_cfg_values()
    error:list[str] = []
    final_cfg_config:dict[str, str|int] = {}
    if len(cfg_config.keys()) != len(default_cfg_config.keys()):
        for v in default_cfg_config.keys():
            if v not in cfg_config.keys():
                error.append(
                    f'"{v}=" Entry not found, check entry "{v}=" is '
                    'present in .cfg file')
    for k, v in cfg_config.items():
        if k in (
            'show_ping', 'connection_lost_recover', 'use_handled_vendors'
        ):
            if v.startswith('ena'):
                final_cfg_config[k] = 'enable'
            elif v.startswith('disa'):
                final_cfg_config[k] = 'disable'
            else:
                error.append(
                    f'Current value in .cfg file: "{k}={v}" -> '
                    f'Entry "{k}", value must be (enable/disable)'
                )
        elif k in (
            'n', 'w', 'l', 'cpu_ping', 'cpu_ssh_telnet', 'port',
            'reload_and_go_timeout', 'connection_lost_timeout', 
            'copy_cmd_delay'
        ):
            if v.isdigit() and int(v) > 0:
                final_cfg_config[k] = int(v)
            else:
                error.append(
                    f'Current value in .cfg file: "{k}={v}" -> '
                    f'Entry "{k}", value must be an integer higher than "0"'
                )
        elif k in ('device_type',):
            if len(v) > 0:
                final_cfg_config[k] = v
            else:
                error.append(
                    f'Current value in .cfg file: "{k}=" -> '
                    f'Entry "{k}", value cannot be empty'
                )
    
    return tuple(error), final_cfg_config

def send_ping(ip:str, n:int=4, l:int=32, w:int=4000, capture_output=True):
    ping_result:CompletedProcess[str] = ping(
        ip=ip, 
        n=n, 
        l=l, 
        w=w, 
        capture_output=capture_output
    )
    
    return ip, ping_result.stdout.strip(), ping_result.returncode

def get_enter_config_mode_keywords():
    # Add most common keywords for enter config mode of different vendors
    keywords:tuple[str] = (
        'conf t', 'configure terminal', 'configure t', 'configure ter',
        'configure', 'config global', 'clish', 'configure system',
        'system-view', 'config'
    )

    return keywords

def command_handler(
        net_connect:BaseConnection, 
        device:dict[str, str|int],
        main_DB:dict[str, str|tuple[str|int]|dict[int, str|int]],
        cfg_config:dict[str, str|int],
        main_thread_lock:Lock
):
    command_list:tuple[str] = main_DB.get('COMMANDS')
    timeout_command_index:dict[int, int] = (
        main_DB.get('TIMEOUT_COMMAND_INDEX')
    )
    config_file_command_index:dict[int, str] = (
        main_DB.get('CONFIG_FILE_COMMAND_INDEX')
    )
    config_mode_command_index:tuple[int] = (
        main_DB.get('CONFIG_MODE_COMMAND_INDEX')
    )
    session_mode:str = main_DB.get('SESSION_MODE')
    files_to_check:tuple[str] = main_DB.get('FILES')
    if cfg_config.get('use_handled_vendors').startswith('ena'):
        handled_vendor:bool = is_vendor_handled(device.get('device_type'))
    else:
        handled_vendor:bool = False
    if cfg_config.get('connection_lost_recover').startswith('ena'):
        try_recover_conn_lost:bool = True
    else:
        try_recover_conn_lost:bool = False
    conn_lost_counter:int = 0
    output_hostname:str = 'Unknown'
    log_commands = fname = ''
    error_reloading = inside_config_mode = inside_enable_mode = False
    prompt_changes_index:list[int] = []
    command_count:int = 0
    # Commands loop start ----------------------------------------------------
    while command_count < len(command_list):
        # Try start ----------------------------------------------------------
        try:
            if command_count == 0: # First iteration
                net_connect.clear_buffer()
                prompt:str = net_connect.find_prompt()
                output_hostname:str = prompt[:-1]
            elif try_recover_conn_lost:
                # check if prompt changed after command performed
                # ONLY commands without return (prompt or text) or commands to enter config mode
                # .find_prompt() will send enter to check prompt, will ruin previous command
                if (
                    output_c.strip() == '' or
                    (command_count-1) in config_mode_command_index
                ):
                    prompt_after_c:str = net_connect.find_prompt()
                    if prompt_after_c != prompt:
                        prompt_changes_index.append(command_count-1) # previous command
                        prompt:str = prompt_after_c
                    inside_enable_mode:bool = net_connect.check_enable_mode()
                    inside_config_mode:bool = net_connect.check_config_mode()
                    if inside_config_mode == False:  # no need to reapply older commands
                        prompt_changes_index:list[int] = []
            c:str = command_list[command_count]  # Commands iterator
            c_timeout:int = timeout_command_index.get(command_count)
            if command_count in config_file_command_index.keys():
                fname:str = config_file_command_index.get(command_count)
            send_command:bool = True
            do_reload = reloading = reload_and_go = enter_and_go = False
            if handled_vendor:  # Pre-command vendor handler
                output_c, send_command, reloading, error_reloading = (
                    vendor_command_handler(
                        net_connect=net_connect,
                        session_mode=session_mode,
                        command=c,
                        command_timeout=c_timeout,
                        output_command='',
                        files_to_check=files_to_check,
                        fname=fname,
                        device=device,
                        send_command=send_command,
                        reloading=reloading,
                        error_reload=error_reloading,
                        main_thread_lock=main_thread_lock,
                        precommand=True
                    )
                )
            # send command start ---------------------------------------------
            if send_command:
                with main_thread_lock:
                    print(
                        f'{" "*2}{session_mode} {device.get("host")} -> '
                        f'Performing command [{fname}{c}]... '
                        f'(timeout: {c_timeout}s)'
                    )
                if c.lower() == 'enter and go':
                    original_c:str = c
                    c:str = ''
                    enter_and_go:bool = True
                    if command_count > 0:
                        if ( # command to send enter to confirm reload
                            're' in command_list[command_count-1].lower() and
                            'and go' in command_list[command_count-1].lower()
                        ):
                            reload_and_go:bool = True
                            do_reload:bool = True
                        elif (
                            'relo' in command_list[command_count-1].lower() or
                            'rest' in command_list[command_count-1].lower() or
                            'rebo' in command_list[command_count-1].lower()
                        ):
                            do_reload:bool = True
                elif 're' in c.lower() and 'and go' in c.lower():
                    original_c:str = c
                    and_go_index:int = c.lower().index('and go')
                    c:str = f'{c[:and_go_index]}{c[and_go_index+6:]}'.strip()
                    reload_and_go:bool = True
                # Main send command start ------------------------------------
                if do_reload: # always c = 'enter and go' to confirm reload
                    try:
                        output_c:str = net_connect.send_command(
                            command_string=c, 
                            read_timeout=c_timeout
                        )
                    except Exception: # if exception, device should be reloading
                        output_c += '\nReload Performed Successfully'
                        error_reloading:bool = False
                        reloading:bool = True
                    else: # command worked, device still on
                        output_c += '\nReload NOT Performed Successfully'
                        error_reloading:bool = True
                        reloading:bool = False
                else:  # ANY other command
                    if (
                        c.lower().startswith('copy') or 
                        c.lower().startswith('do copy')
                    ):
                        with main_thread_lock: # Avoid saturate server copying from
                            time.sleep(
                                float(cfg_config.get('copy_cmd_delay')/1000)
                            )
                    output_c:str = net_connect.send_command_timing(
                        command_string=c, 
                        read_timeout=c_timeout
                    )
                # Main send command end --------------------------------------
                if handled_vendor:  # Post-command vendor handler
                    output_c, send_command, reloading, error_reloading = (
                        vendor_command_handler(
                            net_connect=net_connect,
                            session_mode=session_mode,
                            command=c,
                            command_timeout=c_timeout,
                            output_command=output_c,
                            files_to_check=files_to_check,
                            fname=fname,
                            device=device,
                            send_command=send_command,
                            reloading=reloading,
                            error_reload=error_reloading,
                            main_thread_lock=main_thread_lock,
                            precommand=False
                        )
                    )
                if reload_and_go or enter_and_go:
                    c:str = original_c
                with main_thread_lock:
                    print(
                        f'{" "*2}{session_mode} {device.get("host")} -> '
                        f'Performing command [{fname}{c}]... '
                        f'{colorize("|DONE|", "green")}'
                    )
                if reload_and_go and reloading: # if both true, start reload and go handler
                    reload_timeout:int = (
                        cfg_config.get('reload_and_go_timeout')
                    )
                    zeros:int = len(str(reload_timeout*2))
                    reload_success:bool = False
                    for i in range(reload_timeout*2):
                        with main_thread_lock:
                            print(
                                f'{" "*2}{session_mode} {device.get("host")} '
                                f'-> {colorize("|WAITING|", "cyan")} '
                                f'[{fname}{c}] Device reloading..., '
                                'waiting 30s and doing attempt '
                                f'{str(i+1).zfill(zeros)}/{reload_timeout*2} '
                                'to restablish connection...'
                            )
                        time.sleep(30)
                        try:
                            net_connect.establish_connection()
                        except Exception:
                            continue
                        else:
                            reload_success:bool = True
                            break
                    if reload_success:
                        with main_thread_lock:
                            print(
                                f'{" "*2}{session_mode} {device.get("host")} '
                                f'-> {colorize("|SUCCESS|", "green")} '
                                f'[{fname}{c}] Connection restablished'
                            )
                        net_connect.clear_buffer()
                        prompt:str = net_connect.find_prompt()
                        prompt_changes_index:list[int] = []
                    else:
                        with main_thread_lock:
                            print(
                                f'{" "*2}{session_mode} {device.get("host")} '
                                f'-> {colorize("|TIMEOUT|", "red")} '
                                f'[{fname}{c}] Connection NOT restablished\n'
                                f'{" "*2}{session_mode} {device.get("host")} '
                                f'-> {colorize("|ERROR|", "red")} '
                                f'[{fname}{c}] Aborting SSH Session'
                            )
                        output_c += (
                            f'\n{session_mode} session could NOT '
                            'be restablished.'
                        )
                        error_reloading:bool = True
                if error_reloading:
                    output_c += (
                        f'\nRest of the {session_mode} session ABORTED...'
                    )
            # send command end -----------------------------------------------
            log_commands += (
                f'\n\n{"-"*140}\n[{fname}{c}]\n'
                f'{"#"*130}\n{output_c.strip()}\n{"#"*130}\n{"-"*140}'
            )
            command_count += 1
            conn_lost_counter:int = 0
            if error_reloading:
                break  # exit while (commands loop)
        # Try end ------------------------------------------------------------
        # Except start -------------------------------------------------------
        except Exception:
            with main_thread_lock:
                print(
                    f'{" "*2}{session_mode} {device.get("host")} -> '
                    f'{colorize("|WARNING|", "yellow")} '
                    'Connection to device LOST unexpectedly...'
                )
            conn_restablished:bool = False
            if try_recover_conn_lost and conn_lost_counter < 3:
                with main_thread_lock:
                    print(
                        f'{" "*2}{session_mode} {device.get("host")} -> '
                        f'{colorize("|WARNING|", "yellow")} '
                        'Entry value "connection_lost_recover" in '
                        f'[{main_DB.get("cfg_configNAME")}] is set to '
                        '"enable"...'
                    )
                lost_timeout:int = cfg_config.get('connection_lost_timeout')
                zeros:int = len(str(lost_timeout*4))
                for i in range(lost_timeout*4):
                    with main_thread_lock:
                        print(
                            f'{" "*2}{session_mode} {device.get("host")} -> '
                            f'{colorize("|WAITING|", "cyan")} Waiting 15s '
                            'and doing attempt '
                            f'{str(i+1).zfill(zeros)}/{lost_timeout*4} '
                            'to restablish connection...'
                        )
                    time.sleep(15)
                    try:
                        net_connect.establish_connection()
                    except Exception:
                        continue
                    else:
                        conn_restablished:bool = True
                        break
            if conn_restablished:
                with main_thread_lock:
                    print(
                        f'{" "*2}{session_mode} {device.get("host")} -> '
                        f'{colorize("|SUCCESS|", "green")} '
                        'Connection restablished'
                    )
                conn_lost_counter += 1
                net_connect.clear_buffer()
                if inside_enable_mode:
                    net_connect.enable()
                if inside_config_mode:
                    net_connect.config_mode()
                if len(prompt_changes_index) > 0:
                    for i in prompt_changes_index:
                        net_connect.send_command_timing(
                            command_string=command_list[i], 
                            read_timeout=timeout_command_index.get(i)
                        )
                continue  # continue while (commands loop)
            else:
                if try_recover_conn_lost:
                    if conn_lost_counter < 3:
                        keyword:str = ''
                    else:
                        keyword:str = (
                            f'{" "*2}{session_mode} {device.get("host")} -> '
                            f'{colorize("|ADVICE|", "magenta")} '
                            f'Try command [{fname}{c}] with a <timeout=> '
                            'value higher than '
                            f'"{timeout_command_index.get(command_count)}" '
                            '(seconds)\n'
                        )
                    with main_thread_lock:
                        print(
                            f'{keyword}'
                            f'{" "*2}{session_mode} {device.get("host")} -> '
                            f'{colorize("|TIMEOUT|", "red")} '
                            'Connection NOT restablished\n'
                            f'{" "*2}{session_mode} {device.get("host")} -> '
                            f'{colorize("|ERROR|", "red")} '
                            f'{session_mode} session ABORTED'
                        )
                else:
                    with main_thread_lock:
                        print(
                            f'{" "*2}{session_mode} {device.get("host")} -> '
                            f'{colorize("|WARNING|", "yellow")} '
                            f'Value "connection_lost_recover" in '
                            f'[{main_DB.get('cfg_configNAME')}] is set to '
                            '"disable"...\n'
                            f'{" "*2}{session_mode} {device.get("host")} -> '
                            f'{colorize("|ERROR|", "red")} '
                            f'{session_mode} session ABORTED'
                        )
                banner:str = (
                    ' CONNECTION to device LOST unexpectedly and not '
                    f'restablished. {session_mode} session ABORTED '
                )
                if conn_lost_counter < 3:
                    log_commands += f'\n\n{text_to_box(banner)}'
                else:
                    log_commands += (
                        f'\n\n{text_to_box(banner)}\n'
                        f'Try command [{fname}{c}] with a <timeout=> '
                        'value higher than '
                        f'"{timeout_command_index.get(command_count)}" '
                        '(seconds)'
                    )
                break  # exit while (commands loop)
        # Except end ---------------------------------------------------------
    # Commands loop end ------------------------------------------------------
    if len(command_list) == 0:
        try:
            output_hostname:str = net_connect.find_prompt()[:-1]
        except Exception:
            pass  # output_hostname = 'Unknown', already set at top
        log_commands:str = 'No commands to perform'
    log_device:dict[str, str] = {
        'IP': device.get('host'),
        'HOSTNAME': output_hostname,
        'COMMAND HISTORY': log_commands
    }

    return log_device

def send_ssh_telnet(
        device:dict[str, str|int],
        main_DB:dict[str, str|tuple[str|int]|dict[int, str|int]],
        cfg_config:dict[str, str|int],
        main_thread_lock:Lock
):
    session_mode:str = main_DB.get('SESSION_MODE')
    keyword:str = ""
    try:
        if device.get('device_type').lower() == 'autodetect':
            keyword:str = "autodetected "
            device['device_type'] = SSHDetect(**device).autodetect()
        net_connect:BaseConnection = ConnectHandler(**device)
    except Exception as err:
        err:str = err.__str__().strip().split('\n')[0].strip()
        if err.endswith('.'):
            err:str = err[:-1]
        if 'unsupported' in err.lower() and 'device_type' in err.lower():
            err:str = "Unsupported 'device_type'"
        if keyword:  # keyword:str = 'autodetected '
            device['device_type'] = 'unknown'
        with main_thread_lock:
            print(
                f'{" "*2}{session_mode} {device.get("host")} -> '
                f'{colorize("NOT Established", "red")} '
                f'({keyword}device_type: {device.get("device_type")}) ({err})'
            )
        log_device:dict[str, str] = {
            'IP': device.get('host'),
            'ERR': f'({err})',
            'VENDOR': f'({keyword}device_type: {device.get("device_type")})'
        }
    else:
        with main_thread_lock:
            print(
                f'{" "*2}{session_mode} {device.get("host")} -> '
                f'{colorize("Established...", "green")} '
                f'({keyword}device_type: {device.get("device_type")})'
            )
        log_device:dict[str, str] = command_handler(
            net_connect=net_connect,
            device=device,
            main_DB=main_DB,
            cfg_config=cfg_config,
            main_thread_lock=main_thread_lock
        )
        log_device['VENDOR'] = (
            f'({keyword}device_type: {device.get("device_type")})'
        )
        net_connect.disconnect()
        with main_thread_lock:
            print(
                f'{" "*2}{session_mode} {device.get("host")} -> '
                'Session Finished'
            )

    return log_device