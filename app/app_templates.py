'''
NETWORK_TOOL - Templates data_file.txt and .cfg
'''

# data_file ------------------------------------------------------------------
def default_data_file_values():
    default_data_file:tuple[str] = (
        'USERNAME', 
        'PASSWORD',
        'ENABLE_PASSWORD',
        'HOST',  
        'PING',
        'SSH_TELNET',
        'FILES', 
        'COMMANDS'
    )

    return default_data_file

def template_data_file():
    data_file_text:tuple[str] = (
        '### -USERNAME: Device username (Optional, mandatory if '
        '"-SSH_TELNET:" entry is set to "y")',
        '### -PASSWORD: Device password (Optional, mandatory if '
        '"-SSH_TELNET:" entry is set to "y")',
        '### -ENABLE_PASSWORD: Device enable password (Optional)',
        '### -HOST: Target IP (Mandatory), pings, SSH/Telnet sessions or '
        'both will be performed. You can concatenate unique ip and '
        'ranges(ip_start - ip_end) using ","\n'
        f'{" "*11}(e.g. -> 192.168.1.1 - 192.168.1.5 <step=2>, 192.168.1.8, '
        '192.168.1.10, 192.168.1.15 - 192.168.1.25)\n'
        f'{" "*11}(Step property: You can add '
        'step to ranges e.g. -> 192.168.1.1 - 192.168.1.5 <step=2> -> '
        'only .1, .3, .5 will be used)',
        '### -PING: (Mandatory, y/n), "y" to perform pings, "n" to do not. '
        'If "-SSH_TELNET:" entry is set to "y", program will SSH/Telnet '
        'just to reachable hosts instead of all.',
        '### -SSH_TELNET: (Mandatory, y/n), "y" to perform SSH/Telnet '
        'session, "n" to do not.',
        '### -FILES: (Optional, only Cisco vendor) You can concatenate '
        'filenames using "," (e.g. -> any_filename.any_extension, '
        'WF-TO-SW-05.cfg, ios-17.06.05-SPA.bin)\n'
        f'{" "*12}If copy command, program will check if file is already in '
        'device flash and if yes, it will skip copy command. '
        'Leave blank, will force copy.',
        '### -COMMANDS: Commands to perform (Optional), You will need to '
        'provide commands to enter config mode or exit if needed.\n'
        f'{" "*15}See [handled_vendors.txt] located in "info" directory '
        'in order to know which commands are handled for which vendor.\n'
        f'{" "*15}Typing enter and go will send return/enter to device.\n'
        f'{" "*15}Typing command to reboot + and go (e.g. reload and go), '
        'program will wait SSH/Telnet session to be restablished and will '
        'continue performing commands.\n'
        f'{" "*15}|IMPORTANT| You must use timeout property for commands '
        'based on time, that takes undefined time (more than 10s) '
        'to be completed\n'
        f'{" "*15}<timeout=X> (X value in seconds) e.g. -> '
        'install remove inactive <timeout=300>, '
        'copy tftp://1.1.1.1/any.txt flash: <timeout=1200>\n'
        f'{" "*15}Use files located in "config_files" '
        'directory typing <import=any_filename.txt>, program will import '
        'commands from file "any_filename.txt"'
    )
    max_len:int = 0
    for v in data_file_text:
        if '\n' in v:
            for i in v.split('\n'):
                if len(i) > max_len:
                    max_len:int = len(i)
        else:
            if len(v) > max_len:
                max_len:int = len(v)
    default_data_file:tuple[str] = default_data_file_values()
    template_data_file:str = ''
    for v in data_file_text:
        template_data_file += f'{"-"*(max_len)}\n{v}\n'
    template_data_file += (
        f'{"-"*(max_len)}\n\n'
        f'-{default_data_file[0]}: \n'
        f'-{default_data_file[1]}: \n'
        f'-{default_data_file[2]}: \n'
        f'-{default_data_file[3]}: \n'
        f'-{default_data_file[4]}: y\n'
        f'-{default_data_file[5]}: y\n'
        f'-{default_data_file[6]}: \n\n'
        f'-{default_data_file[7]}: Paste your commands below. '
        'One command per line. Do not delete this line.\n\n'
    )

    return template_data_file

# cfg_file -------------------------------------------------------------------
def default_cfg_values():
    default_cfg:dict[str, str|int] = {
        'n': 2,
        'w': 1000,
        'l': 32,
        'show_ping': 'disable',
        'cpu_ping': 250,
        'device_type': 'autodetect',
        'port': 22,
        'use_handled_vendors': 'enable',
        'connection_lost_recover': 'enable',
        'connection_lost_timeout': 1,
        'reload_and_go_timeout': 10,
        'cpu_ssh_telnet': 40
    }

    return default_cfg

def default_cfg_values_string():
    default_cfg_db:dict[str, str|int] = default_cfg_values()
    string_cfg_file_db:str = ''
    for k, v in default_cfg_db.items():
        string_cfg_file_db += f'[{k}: {v}], '
        if k in (
            'cpu_ping', 'use_handled_vendors', 'connection_lost_timeout'
        ):
            string_cfg_file_db += f'\n{" "*18}' # len('DEFAULT values -> ') = 18
    string_cfg_file_db:str = string_cfg_file_db.strip()[:-1]

    return string_cfg_file_db

def template_cfg_file():
    ping_text:tuple[str] = (
        '"n" -> Number of ping packets to send',
        '"w" -> (Miliseconds) time to wait for ping packet replies',
        '"l" -> (Bytes) ping packet size',
        '"show_ping" -> Show ping process and result (enable) or '
        'just result (disable)',
        '"cpu_ping" -> Max number of threads cpu will use to perform '
        'asynchronous pings'
    )
    ssh_text:tuple[str] = (
        '"device_type" -> Device vendor for SSH/Telnet session. Look at file '
        '[device_type_supported_PLATFORMS.txt] in "info" directory',
        '"port" -> Port to perform SSH/Telnet session',
        '"use_handled_vendors" -> (enable) to use vendor command handler, '
        '(disable) to do not. See [handled_vendors.txt] in info directory',
        '"connection_lost_recover" -> Try to recover SSH/Telnet session if '
        'connection is lost (enable) or not to try (disable)',
        '"connection_lost_timeout" -> (Minutes) Max timer to restablish '
        'SSH/Telnet session if connection is lost',
        '"reload_and_go_timeout" -> (Minutes) Max timer to restablish '
        'SSH/Telnet session after command to reboot + "and go" was performed',
        '"cpu_ssh_telnet" -> Max number of threads cpu will use to '
        'perform asynchronous SSH/Telnet sessions'
    )
    all_boxed_texts:list[str] = []
    for text in (ping_text, ssh_text):
        max_len:int = 0
        for v in text:
            if len(v) > max_len:
                max_len:int = len(v)
        boxed_text:str = f'{" "*2}{"-"*(max_len+4)}'
        for v in text:
            boxed_text += f'\n{" "*2}| {v.ljust(max_len)} |'
        boxed_text += f'\n{" "*2}{"-"*(max_len+4)}'
        all_boxed_texts.append(boxed_text)
    default_cfg:dict[str, str|int] = default_cfg_values()
    template_cfg_file:str = (
        '### PING OPTIONS ###\n'
        f'{all_boxed_texts[0]}\n'
        f'{" "*2}n={default_cfg.get("n")}\n'
        f'{" "*2}w={default_cfg.get("w")}\n'
        f'{" "*2}l={default_cfg.get("l")}\n'
        f'{" "*2}show_ping={default_cfg.get("show_ping")}\n'
        f'{" "*2}cpu_ping={default_cfg.get("cpu_ping")}\n\n\n'
        '### SSH/TELNET OPTIONS ###\n'
        f'{all_boxed_texts[1]}\n'
        f'{" "*2}device_type={default_cfg.get("device_type")}\n'
        f'{" "*2}port={default_cfg.get("port")}\n'
        f'{" "*2}use_handled_vendors='
        f'{default_cfg.get("use_handled_vendors")}\n'
        f'{" "*2}connection_lost_recover='
        f'{default_cfg.get("connection_lost_recover")}\n'
        f'{" "*2}connection_lost_timeout='
        f'{default_cfg.get("connection_lost_timeout")}\n'
        f'{" "*2}reload_and_go_timeout='
        f'{default_cfg.get("reload_and_go_timeout")}\n'
        f'{" "*2}cpu_ssh_telnet='
        f'{default_cfg.get("cpu_ssh_telnet")}\n\n\n'
        f'DEFAULT values -> {default_cfg_values_string()}'
    )

    return template_cfg_file