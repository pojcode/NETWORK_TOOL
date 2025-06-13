'''
NETWORK_TOOL -- App Templates
'''


# data_file ------------------------------------------------------------------
def get_default_data_file_values():
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

def get_template_data_file():
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
        f'{" "*15}Typing "enter and go" will send return/enter to device.\n'
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
    default_data_file:tuple[str] = get_default_data_file_values()
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
def get_default_cfg_values():
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
        'copy_cmd_delay': 1000,
        'cpu_ssh_telnet': 50
    }

    return default_cfg

def get_default_cfg_values_string():
    default_cfg_db:dict[str, str|int] = get_default_cfg_values()
    string_cfg_file_db:str = ''
    for k, v in default_cfg_db.items():
        string_cfg_file_db += f'[{k}: {v}], '
        if k in (
            'cpu_ping', 'use_handled_vendors', 'connection_lost_timeout'
        ):
            string_cfg_file_db += f'\n{" "*18}' # len('DEFAULT values -> ') = 18
    string_cfg_file_db:str = string_cfg_file_db.strip()[:-1]  # Avoid last ","

    return string_cfg_file_db

def get_template_cfg_file():
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
        '"copy_cmd_delay" -> (Miliseconds) Delay applied to copy commands'
        ' avoiding saturate server copying from',
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
    default_cfg:dict[str, str|int] = get_default_cfg_values()
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
        f'{" "*2}copy_cmd_delay='
        f'{default_cfg.get("copy_cmd_delay")}\n'
        f'{" "*2}cpu_ssh_telnet='
        f'{default_cfg.get("cpu_ssh_telnet")}\n\n\n'
        f'DEFAULT values -> {get_default_cfg_values_string()}'
    )

    return template_cfg_file

# Readme files for config_files and logs folders -----------------------------
def get_template_readme_config_files():
    template_readme_config_files:str = (
        '### CREATE AND IMPORT CONFIG FILES ###\n\n'
        '- Create a .txt file.\n\n'
        '- Type your commands, one command per line. Line starting with # '
        'will be considered as comment.\n'
        f'{" "*2}|IMPORTANT| Do not forget to type <timeout=X> '
        '(X -> value in seconds) for commands that take undefined time '
        '(more than 10s) to be completed.\n\n'
        '- Place your file in "config_files" directory.\n\n'
        '- Import file typing <import=your_filename.txt> in "-COMMANDS:" '
        'entry section, located inside data_file.txt'
    )

    return template_readme_config_files

def get_template_readme_logs():
    template_readme_logs:str = (
        '### LOG FILES ###\n\n'
        'After program ends successfully, a log file will be created.\n\n'
        'Log file filename will be based on -> '
        'year-month-day_hours.minutes.seconds_main_filename_log.txt'
    )

    return template_readme_logs

# Rest of the files ----------------------------------------------------------
def get_template_how_to_use_file():
    template_how_to_use_file:str = (
        '### HOW TO USE ###\n\n'
        '- Fill in data_file.txt with the data required\n'
        '- Save data_file.txt\n'
        '- Run program\n\n'
        'You can modify parameters for pings and SSH/Telnet sessions '
        'using .cfg file.\n\n'
        'Understanding "device_type" entry in .cfg file (See '
        '[device_type_supported_PLATFORMS.txt] located in "info" directory '
        'to get more info):\n\n'
        f'{" "*4}Connection mode (SSH/Telnet) is based on "device_type" '
        'value configured in .cfg file.\n'
        f'{" "*4}Selecting a device_type with "telnet" keyword will perform '
        'Telnet, else SSH.\n\n'
        f'{" "*4}- SSH:\n'
        f'{" "*8}device_type: autodetect -> Program will detect the best '
        'match to set device_type and perform SSH session.\n'
        f'{" "*8}device_type: generic -> Program will use generic settings '
        'to perform SSH session. Use only if you do not know target '
        'device vendor.\n'
        f'{" "*8}device_type: cisco_ios -> Program will use cisco_ios '
        'settings to perform SSH session. If target device device_type is not '
        'cisco_ios, SSH will fail.\n\n'
        f'{" "*4}- TELNET:\n'
        f'{" "*8}device_type: generic_telnet -> Program will use generic '
        'settings to perform TELNET session. Use only if you do not know '
        'target device vendor.\n'
        f'{" "*8}device_type: cisco_ios_telnet -> Program will use cisco_ios '
        'settings to perform TELNET session. If target device device_type '
        'is not cisco_ios, TELNET will fail.\n\n'
        f'{" "*4}Using generic device_types (generic, generic_telnet), '
        'may cause issues performing SSH/Telnet sessions (especially '
        'generic_telnet). Use at your own risk.\n\n'
        'You can place files containing commands in "config_files" directory '
        'and use that files to apply the commands contained in them.\n'
        '(e.g in data_file.txt -> -COMMANDS: -> <import=filename.txt> -> '
        'program will take commands from filename.txt and will apply '
        'them to devices)\n\n'
        'A log file located in "logs" directory will be created after '
        'program ends successfully.\n\n'
        'If you run program and any file is missing, program will create '
        'them automatically with default values.'
    )

    return template_how_to_use_file

def get_template_readme_file():
    readme_table_text:tuple[str] = (
        'NETWORK TOOL to perform pings and SSH/Telnet sessions to multiple '
        'devices simultaneously',
        f'{" "*2}- Multi-vendor',
        f'{" "*2}- Compatibility with IPv4 and IPv6',
        f'{" "*2}- Support for external config files',
        f'{" "*2}- Support different settings for asynchronous pings and '
        'SSH/Telnet sessions',
        f'{" "*2}- A log file (.txt) will be generated after program ends',
        f'{" "*2}- Many more settings and features...'
    )
    max_len:int = 0
    for v in readme_table_text:
        if len(v) > max_len:
            max_len:int = len(v)
    boxed_text:str = "-"*(max_len+4)
    for v in readme_table_text:
        boxed_text += f'\n| {v.ljust(max_len)} |'
    boxed_text += f'\n{"-"*(max_len+4)}'
    template_readme_file:str = (
        f'{boxed_text}\n\n'
        'NETWORK TOOL project -> https://github.com/pojcode/NETWORK_TOOL\n\n'
        'LINUX, MAC users:\n'
        f'{" "*4}You must use Python v3.13.2 or onwards to run program\n'
        f'{" "*4}Lower Python versions could run program but not tested\n\n'
        f'{" "*4}Download Python here or use your packet manager, up to you\n'
        f'{" "*4}https://www.python.org\n\n'
        f'{" "*4}You will need 3rd party Python libs from Pypi repository '
        'installed in your device (Netmiko, Art, and Colorama)\n'
        f'{" "*8}open shell and cd to program directory\n'
        f'{" "*8}run in shell -> python3 -m pip install -r '
        'requirements.txt\n\n'
        'Special thanks to ktbyers for Netmiko lib, sepandhaghighi for Art '
        'lib and tartley for Colorama lib.\n\n\n'
        f'{" "*24}Created by POJ'
    )

    return template_readme_file

def get_template_requirements_file():
    template_requirements_file:str = (
        'art==6.5\n'
        'colorama==0.4.6\n'
        'netmiko==4.5.0'
    )

    return template_requirements_file