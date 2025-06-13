'''
Main for NETWORK_TOOL
'''

import os, sys, concurrent.futures, time, datetime
from threading import Lock
from colorama import init, deinit
from app.network import create_ip_range, sort_ip
from app.utils import (
    colorize, get_banner_title_font, create_banner_title, text_to_box
)
from app.system import (
    get_OS_path_separator, clear_console, load_file, save_file, create_dir
)
from app.app import (
    create_db, create_data_table, validate_db, validate_db_host_info, 
    import_config_file, get_enter_config_mode_keywords, get_command_timeout,
    create_cfg, validate_cfg, send_ping, send_ssh_telnet
)
from app.templates import (
    get_template_data_file, get_default_cfg_values, 
    get_template_cfg_file, get_default_cfg_values_string, 
    get_template_readme_config_files, get_template_readme_logs,
    get_template_how_to_use_file, get_template_readme_file, 
    get_template_requirements_file
)


def main():
    # Create main path, separator for other paths and filenames --------------
    MAIN_PATH:str = os.getcwd()
    MAIN_FILE:str = os.path.basename(sys.argv[0])
    for i, ch in enumerate(MAIN_FILE):
        if ch == '.':  # search for dot just before file extension
            dot:int = i
    DATA_FILE:str = f'{MAIN_FILE[:dot]}_data_file.txt'
    CFG_FILE:str = f'{MAIN_FILE[:dot]}.cfg'
    SEP:str = get_OS_path_separator()  # separator for paths
    # Clear console screen, create and print program banner title ------------
    clear_console()
    init(autoreset=True)  # init for colorama
    banner_title:str = create_banner_title(
        title=MAIN_FILE[:dot], 
        font=get_banner_title_font(font='random'),
        style='bright'
    )
    banner_tip:str = (
        f' {MAIN_FILE} running || Exit program pressing "Ctrl+C" '
        'or closing window at any time '
    )
    print(f'{banner_title}\n{text_to_box(banner_tip, box_line="=")}\n')
    # Load data_file.txt, .cfg file, config_files folder and logs folder -----
    if DATA_FILE in os.listdir(MAIN_PATH):
        show_load_files_process:bool = False  # load files in background
    else:
        show_load_files_process:bool = True  # load files on display
    mandatory_loaded_files:dict[str, tuple[str]] = {}
    if show_load_files_process:
        print(text_to_box(' LOADING ALL NECESSARY FILES... '))
    for file in (DATA_FILE, CFG_FILE, 'config_files', 'logs'):
        if file in (DATA_FILE, CFG_FILE):  # Files
            if show_load_files_process:
                print(f'\n{" "*2}- Loading file [{file}]... -> ', end='')
            try:
                data_raw:tuple[str] = load_file(file, MAIN_PATH)
            except FileNotFoundError:
                if file == DATA_FILE:
                    template_text:str = get_template_data_file()
                    keyword:str = f'blank [{file}]'
                else:
                    template_text:str = get_template_cfg_file()
                    keyword:str = f'[{file}] with default values'
                if show_load_files_process:
                    print(colorize('|ERROR|', 'red'))
                    print(
                        f'{" "*4}{colorize("|WARNING|", "yellow")} '
                        f'File [{file}] not found...\n{" "*4}Creating '
                        f'{keyword}... -> ',
                        end=''
                    )
                save_file(file, template_text, MAIN_PATH)
                if show_load_files_process:
                    print(colorize('|DONE|', 'green'))
            else:
                mandatory_loaded_files[file] = data_raw
                if show_load_files_process:
                    print(colorize('|DONE|', 'green'))
        elif file in ('config_files', 'logs'):  # Directories
            if show_load_files_process:
                print(f'\n{" "*2}- Loading directory "{file}"... -> ', end='')
            try:
                create_dir(file, MAIN_PATH)
            except FileExistsError:
                if show_load_files_process:
                    print(colorize('|DONE|', 'green'))
            else:
                if show_load_files_process:
                    print(colorize('|ERROR|', 'red'))
                    print(
                        f'{" "*4}{colorize("|WARNING|", "yellow")} '
                        f'Directory "{file}" not found...\n'
                        f'{" "*4}Creating directory "{file}"... -> '
                        f'{colorize("|DONE|", "green")}'
                    )
    # Check other files, create them if not present --------------------------
    for file in ('how_to_use.txt', 'readme.txt', 'requirements.txt', 
                 'readme_config_files.txt', 'readme_logs.txt'):
        folder_path:str = ''
        if file == 'how_to_use.txt':
            template_text:str = get_template_how_to_use_file()
        elif file == 'readme.txt':
            template_text:str = get_template_readme_file()
        elif file == 'requirements.txt':
            template_text:str = get_template_requirements_file()
        elif file == 'readme_config_files.txt':
            template_text:str = get_template_readme_config_files()
            folder_path:str = f'{SEP}config_files'
        elif file == 'readme_logs.txt':
            template_text:str = get_template_readme_logs()
            folder_path:str = f'{SEP}logs'
        try:
            save_file(file, template_text, f'{MAIN_PATH}{folder_path}', 'x')
        except FileExistsError:
            continue
    # Continue program if data_file.txt is loaded not created ----------------
    if DATA_FILE not in mandatory_loaded_files.keys():  # data_file created
        print(
            f'\n\nFill in [{DATA_FILE}] with the data required and run '
            f'[{MAIN_FILE}] again'
        )
        input('\nPress Enter to exit program...')
        exit()
    elif CFG_FILE not in mandatory_loaded_files.keys():  # .cfg created
        cfg_file_was_created:bool = True
    else:  # None created, data_file and .cfg loaded
        cfg_file_was_created:bool = False
    # Create temporal main_DB and print a table with the data ---------------
    raw_data_file:tuple[str] = mandatory_loaded_files.get(DATA_FILE)
    temp_main_DB:dict[str, str|tuple[str]] = create_db(raw_data_file)
    data_file_table:str = create_data_table(
        values=temp_main_DB, 
        title=f'[{DATA_FILE}]'
    )
    print(data_file_table)
    # Check main_DB entries and set main_DB without errors -----------------
    error_list:list[str] = []
    error, main_DB = validate_db(temp_main_DB)
    error_list.extend(error)
    # Check, validate and manage HOST IP info --------------------------------
    host_data_list:list[tuple[str]] = []
    for ip_or_range in main_DB.get('HOST'):
        error, data = validate_db_host_info(ip_or_range)
        error_list.extend(error)
        host_data_list.append(data)
    main_DB['HOST_DATA'] = tuple(host_data_list)
    # Check config files - If present add commands to commands list ----------
    config_file_path:str = f'{MAIN_PATH}{SEP}config_files'
    config_file_command_index:dict[int, str] = {}
    final_command_list:list[str] = []
    for c in main_DB.get('COMMANDS'):
        if '<import=' in c.lower():
            error, config_file_info = import_config_file(c, config_file_path)
            error_list.extend(error)
            for k, v in config_file_info.items():
                filename:str = f'{k}: '  # k = filename, used for command info in log
                config_file_command_index[len(final_command_list)] = filename
                final_command_list.extend(v)  # v = Command list contained in file
                config_file_command_index[len(final_command_list)] = ''
        else:
            final_command_list.append(c)
    main_DB['CONFIG_FILE_COMMAND_INDEX'] = config_file_command_index
    # Set all data related to command list -----------------------------------
    fname:str = ''
    timeout_command_index:dict[int, int] = {}
    enter_config_mode_keywords:tuple[str] = get_enter_config_mode_keywords()
    config_mode_command_index:list[int] = []
    for i, c in enumerate(final_command_list):
        if '<timeout=' in c.lower():
            if i in config_file_command_index.keys():
                fname:str = config_file_command_index.get(i)
            error, command_data = get_command_timeout(c, fname)
            error_list.extend(error)
            del final_command_list[i]
            final_command_list.insert(i, command_data[0])
            timeout_command_index[i] = command_data[1]
            if command_data[0].lower() in enter_config_mode_keywords:
                config_mode_command_index.append(i)
        else:
            timeout_command_index[i] = 10  # default timeout for commands
            if c.lower() in enter_config_mode_keywords:
                config_mode_command_index.append(i)
    main_DB['COMMANDS'] = tuple(final_command_list)
    main_DB['TIMEOUT_COMMAND_INDEX'] = timeout_command_index
    main_DB['CONFIG_MODE_COMMAND_INDEX'] = tuple(config_mode_command_index)
    # Print and manage errors or prompt user to continue ---------------------
    if len(error_list) > 0:
        zeros:int = len(str(len(error_list)))
        print()
        for i, err in enumerate(error_list):
            error_banner:str = f"|ERROR {str(i+1).zfill(zeros)}|"
            print(f'{colorize(error_banner, "red")} [{DATA_FILE}] {err}')
        input('\nPress Enter to exit program...')
        exit()
    else:
        input(
            f'\nIf [{colorize(DATA_FILE, "green")}] data is '
            f'{colorize("OK", "green")}, press Enter to continue...'
        )
        time_start:float = time.time()
    # Manage .cfg file -------------------------------------------------------
    cfg_config:dict[str, str|int] = get_default_cfg_values()
    error_list:list[str] = []
    if cfg_file_was_created == False:  # validate .cfg only if it was loaded
        raw_cfg_file:tuple[str] = mandatory_loaded_files.get(CFG_FILE)
        temp_cfg_config:dict[str, str] = create_cfg(raw_cfg_file)
        error, final_temp_cfg_config = validate_cfg(temp_cfg_config)
        error_list.extend(error)
    if len(error_list) > 0:
        print(
            f'\n{colorize("|WARNING|", "yellow")} '
            f'File [{CFG_FILE}] contains syntax errors:\n'
        )
        zeros:int = len(str(len(error_list)))
        for i, err in enumerate(error_list):
            error_banner:str = f'|ERROR {str(i+1).zfill(zeros)}|'
            print(f'{" "*2}{colorize(error_banner, "red")} {err}')
        valid_cfg:bool = False  # prompt user to continue or not
    else: # no errors or .cfg created with def values during program execution
        if cfg_file_was_created:
            valid_cfg:bool = False   # prompt user to continue or not
        else:
            valid_cfg:bool = True
            for k, v in final_temp_cfg_config.items():
                cfg_config[k] = v  # set values according to valid loaded .cfg
    if valid_cfg:
        esp:int = len(f'Using [{CFG_FILE}] -> ')
        string_cfg_config:str = ''
        for k, v in cfg_config.items():
            string_cfg_config += f'[{k}: {v}], '
            if k in (
                'cpu_ping', 'use_handled_vendors', 'connection_lost_timeout'
            ):
                string_cfg_config += f'\n{" "*esp}'
        string_cfg_config:str = string_cfg_config.strip()[:-1]
        print(
            f'\nUsing [{colorize(CFG_FILE, "green")}] -> '
            f'{string_cfg_config}\n'
        )
        cfg_to_log:str = f'Using [{CFG_FILE}] -> {string_cfg_config}'
    else:
        string_cfg_config:str = get_default_cfg_values_string()
        if cfg_file_was_created:
            print(
                f'\n{colorize("|WARNING|", "yellow")} [{CFG_FILE}] was '
                f'not found and it was created during [{MAIN_FILE}] '
                'execution...'
            )
        print(
            f'\n{colorize("DEFAULT", "green")} values -> '
            f'{string_cfg_config}\n'
        )
        pos:int = 0
        for i in range(string_cfg_config.count('\n')):
            index_n:int = string_cfg_config.index('\n', pos)
            string_cfg_config:str = (
                f'{string_cfg_config[:index_n+2]}{" "*6}' # len("Using ") = 6
                f'{string_cfg_config[index_n+2:]}'
            )
            pos:int = index_n + 1
        cfg_to_log:str = f'Using DEFAULT values -> {string_cfg_config}'
        while True:
            resp:str = input(
                f'{" "*2}{colorize(">>", "magenta")} Continue using '
                f'{colorize("DEFAULT", "green")} values? (y/n) -> '
            )
            if resp.lower() in ('y', 'ye', 'yes'):
                print(f'\nUsing {colorize("DEFAULT", "green")} values...\n')
                break
            elif resp.lower() in ('n', 'no'):
                input('\nPress Enter to exit program...')
                exit()
            else:
                print('\tInvalid Option...\n')
                time.sleep(2)
    # Create HOST IP list ----------------------------------------------------
    print('Creating HOST IP list... ', end='')
    ip_list:list[str] = []
    ip_data:tuple[tuple[str]] = main_DB.get('HOST_DATA')
    for v in ip_data:
        if len(v) == 1:  # Unique IP (ip_start,)
            ip_list.append(v[0])
        else:  # len(v) = 3, IP range -> (ip_start, ip_end, step)
            ip_range:tuple[str] = create_ip_range(v[0], v[1], int(v[2]))
            ip_list.extend(ip_range)
    total_host_list:tuple[str] = sort_ip(set(ip_list))
    print(f'{colorize("|DONE|", "green")}\n')
    # Initialize log variables -----------------------------------------------
    session_log:str = ''
    global_summary_log:str = f'{text_to_box(" GLOBAL SUMMARY ")}\n'
    # Pings ------------------------------------------------------------------
    if main_DB.get('PING').lower() in ('y', 'ye', 'yes'):
        print(f'\n{text_to_box("## STARTING HOST PINGS ##")}\n')
        print(
            f'{" "*2}-| Total PINGS: '
            f'{colorize(str(len(total_host_list)), "green")}  ---  '
            f'Simultaneous PINGS: '
            f'{colorize(str(cfg_config.get("cpu_ping")), "green")} |-'
        )
        session_log += f'\n\n{text_to_box(" HOST PING SUMMARY ")}\n'
        futures:list[concurrent.futures.Future] = []
        ping_list:list[tuple[str, str, int]] = []
        with (
            concurrent.futures.ThreadPoolExecutor(
                max_workers=cfg_config.get('cpu_ping')
            ) as exec
        ):
            for ip in total_host_list:
                futures.append(
                    exec.submit(
                        send_ping, 
                        ip=ip, 
                        n=cfg_config.get('n'),
                        l=cfg_config.get('l'),
                        w=cfg_config.get('w')  
                    )
                )
            for future in concurrent.futures.as_completed(futures):
                ping_list.append(future.result())
        sorted_ping_list:list[str] = []
        for v in ping_list:
            sorted_ping_list.append(v[0])
        final_sorted_ping:tuple[str] = sort_ip(sorted_ping_list)
        final_ping_list:list[tuple[str, str, int]] = []
        for ip in final_sorted_ping:
            for i, v in enumerate(tuple(ping_list)):
                if ip == v[0]:
                    final_ping_list.append(v)
                    del ping_list[i]
                    break
        pingable_host_list:list[str] = []
        ping_result_banner:str = ''
        for data in tuple(final_ping_list):
            if 'ttl' in data[1].lower() and data[2] == 0:
                status:str = "Successful"
                color:str = "green"
                pingable_host_list.append(data[0])
            else:
                status:str = "NOT Replying"
                color:str = "red"
            session_log += f'\n\t- Ping HOST {data[0]} -> {status}'
            ping_result_banner += (
                f'\n{" "*2}Ping HOST {data[0]} -> {colorize(status, color)}'
            )
            if cfg_config.get('show_ping').startswith('ena'):
                # show_ping is enabled, manage and show ping processes
                this_ping_process:list[str] = data[1].strip().split('\n')
                session_log += f'\n\t{" "*2}{"-"*60}'
                ping_result_banner += f'\n{" "*7}{"-"*60}'
                for line in this_ping_process:
                    session_log += f'\n\t{" "*2}{line.strip()}'
                    ping_result_banner += f'\n{" "*7}{line.strip()}'
                session_log += f'\n\t{" "*2}{"-"*60}\n'
                ping_result_banner += f'\n{" "*7}{"-"*60}\n'
        session_log:str = session_log.rstrip()
        ping_result_banner:str = ping_result_banner.rstrip()
        print(ping_result_banner)
        global_summary_log += (
            f'\n\t- TOTAL HOST PINGS -> {len(total_host_list)}'
            f'{" "*6}- SUCCESSFUL HOST PINGS -> {len(pingable_host_list)}'
        )
        not_replying_host:int = len(total_host_list) - len(pingable_host_list)
        print(
            f'\n{" "*2}-| PINGS SUMMARY ->  Successful: '
            f'{colorize(str(len(pingable_host_list)), "green")}  ---  '
            'NOT Replying: '
            f'{colorize(str(not_replying_host), "red")} |-'
        )
        print(f'\n{text_to_box("## HOST PINGS DONE ##")}')
    else:
        print(f'\n{text_to_box("## HOST PINGS SKIPPED... ##")}')
        session_log += f'\n\n{text_to_box(" HOST PINGS SKIPPED ")}'
    # SSH/Telnet sessions ----------------------------------------------------
    if main_DB.get('SSH_TELNET').lower() in ('y', 'ye', 'yes'):
        if 'telnet' in cfg_config.get('device_type').lower():
            keyword:str = "TELNET"
        else:
            keyword:str = "SSH"
        print(f'\n{text_to_box(f"## STARTING {keyword} SESSIONS ##")}\n')
        session_log += f'\n\n{text_to_box(f" {keyword} SESSION SUMMARY ")}\n'
        main_DB['SESSION_MODE'] = keyword  # Used with command handler
        main_DB['CFG_FILENAME'] = CFG_FILE  # Used with command handler
        if main_DB.get('PING').lower() in ('y', 'ye', 'yes'):
            total_session_list:tuple[str] = tuple(pingable_host_list)
        else:
            total_session_list:tuple[str] = total_host_list 
        counter:int = 0
        if len(total_session_list) > 0:
            print(
                f'{" "*2}-| Total {keyword} Sessions: '
                f'{colorize(str(len(total_session_list)), "green")}  ---  '
                f'Simultaneous {keyword} Sessions: '
                f'{colorize(str(cfg_config.get("cpu_ssh_telnet")), "green")}'
                f' |-\n{" "*2}-| Entry value '
                f'"{colorize("device_type", "green")}" in '
                f'[{colorize(CFG_FILE, "green")}] is set to '
                f'"{colorize(str(cfg_config.get("device_type")), "green")}"'
                f' |-\n{" "*2}-| Using PORT: '
                f'{colorize(str(cfg_config.get("port")), "green")} |-\n'
            )
            main_thread_lock:Lock = Lock()
            futures:list[concurrent.futures.Future] = []
            session_list:list[dict[str, str]] = []
            with (
                concurrent.futures.ThreadPoolExecutor(
                    max_workers=cfg_config.get('cpu_ssh_telnet')
                ) as exec
            ):
                for ip in total_session_list:
                    device_template:dict[str, str|int] = {
                        'device_type': cfg_config.get('device_type'),
                        'host': ip,
                        'username': main_DB.get('USERNAME'),
                        'password': main_DB.get('PASSWORD'),
                        'secret': main_DB.get('ENABLE_PASSWORD'),
                        'port': cfg_config.get('port')
                    }
                    futures.append(
                        exec.submit(
                            send_ssh_telnet, 
                            device=device_template,
                            main_DB=main_DB, 
                            cfg_config=cfg_config,
                            main_thread_lock=main_thread_lock
                        )
                    )
                for future in concurrent.futures.as_completed(futures):
                    session_list.append(future.result())
            sorted_session_list:list[str] = []
            for v in session_list:
                sorted_session_list.append(v.get('IP'))
            final_sorted_session:tuple[str] = sort_ip(sorted_session_list)
            final_session_list:list[dict[str, str]] = []
            for ip in final_sorted_session:
                for i, v in enumerate(tuple(session_list)):
                    if ip == v.get('IP'):
                        final_session_list.append(v)
                        del session_list[i]
                        break
            devices_log:str = ''
            for data in tuple(final_session_list):
                if 'ERR' in data.keys():
                    status:str = (
                        f'NOT Established {data.get("VENDOR")} '
                        f'{data.get("ERR")}'
                    )
                else:
                    status:str = f'Established {data.get("VENDOR")}'
                    counter += 1
                    devices_log += f'{"="*150}'
                    for k, v in data.items():
                        if k != 'VENDOR':
                            devices_log += f'\n{k}: {v}'
                    devices_log += f'\n{"="*150}\n\n'
                session_log += f'\n\t- {keyword} {data.get("IP")} -> {status}'
            if devices_log:
                session_log += (
                    f'\n\n{text_to_box(f" {keyword} COMMAND SUMMARY ")}\n\n'
                    f'{devices_log.rstrip()}'
                )
            print(
                f'\n{" "*2}-| {keyword} SUMMARY ->  Established: '
                f'{colorize(str(counter), "green")}  ---  '
                'NOT Established: '
                f'{colorize(str(len(total_session_list)-counter), "red")} |-'
            )
        else:
            print(
                f'{" "*2}No {keyword} session due to any HOST IP is reachable'
            )
            session_log += (
                f'\n\t- No {keyword} session due to any HOST IP is reachable'
            )
        global_summary_log += (
            f'\n\t- TOTAL {keyword} SESSIONS -> {len(total_session_list)}'
            f'{" "*6}- ESTABLISHED {keyword} SESSIONS -> {counter}'
        )
        print(f'\n{text_to_box(f"## {keyword} SESSIONS DONE ##")}')
    # Save program log in to a .txt file and end program ---------------------
    log_file_path:str = f'{MAIN_PATH}{SEP}logs'
    time_total:float = time.time() - time_start
    if time_total >= 60:
        time_total:float = time_total / 60
        time_unit:str = 'minutes'
    else:
        time_unit:str = 'seconds'
    run_time:str = f'Program running time: {time_total:.2f} {time_unit}'
    print('\n\nCreating log file... ', end='')
    date_obj:datetime.datetime = datetime.datetime.now()
    log_filename:str = (
        f'{date_obj.strftime(f"%Y-%m-%d_%H.%M.%S")}_{MAIN_FILE[:dot]}_log.txt'
    )
    date:str = f'Log created: {date_obj.strftime(f"%A %d %B %Y - %H:%M:%S")}'
    log_to_export:str = (
        f'---| {date}{" "*3}||{" "*3}{run_time} |---\n\n{data_file_table}\n\n'
        f'{cfg_to_log}\n\n{global_summary_log}{session_log.rstrip()}'
    )
    try:
        save_file(log_filename, log_to_export, log_file_path)
    except Exception as err:
        print(f'{colorize("|ERROR|", color="red")}')
        print(
            f'\n{colorize("|ERROR|", "red")} --- Log file -> '
            f'[logs{SEP}{log_filename}] could NOT be '
            f'created ({err})'
        )
    else:
        print(f'{colorize("|DONE|", color="green")}')
        print(
            f'\nLog file created successfully -> [logs{SEP}'
            f'{colorize(log_filename, "green")}]'
        )
    print(f'\n--- {run_time} ---')
    deinit()  # deinit for colorama
    input('\nPress Enter to exit program...')