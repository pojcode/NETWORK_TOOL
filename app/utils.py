'''
Visual and others related functions
'''

import random
from colorama import Fore, Style
from art import text2art


def get_colors_styles():
    colors_DB:dict[str, str] = {
        'green': Fore.LIGHTGREEN_EX,
        'red': Fore.LIGHTRED_EX,
        'yellow': Fore.LIGHTYELLOW_EX,
        'magenta': Fore.LIGHTMAGENTA_EX,
        'cyan': Fore.LIGHTCYAN_EX,
        'blue': Fore.LIGHTBLUE_EX
    }
    styles_DB:dict[str, str] = {
        'dim': Style.DIM,
        'normal': Style.NORMAL,
        'bright': Style.BRIGHT
    }

    return colors_DB, styles_DB

def colorize(text:str, color:str, style:str='normal'):
    colors_DB, styles_DB = get_colors_styles()
    chosen_color = chosen_style = ''
    if color in colors_DB.keys():
        chosen_color:str = colors_DB.get(color)
    if style in styles_DB.keys():
        chosen_style:str = styles_DB.get(style)
    colorized_string:str = (
        f'{chosen_style}{chosen_color}{text}{Style.RESET_ALL}'
    )
    
    return colorized_string

def get_banner_title_font(font:str='random'):
    title_fonts:tuple[str] = ('avatar', 'big', 'cricket', 'graffiti', 'pawp')
    if font.strip().lower().startswith('rand'): # Random font
        chosen_font:str = random.choice(title_fonts)
    elif font.strip().lower() in title_fonts:  # Especific font
        chosen_font:str = font.strip().lower()
    else:  # font error or font not available
        chosen_font:str = 'graffiti' # Default font
    
    return chosen_font

def create_banner_title(title:str, font:str, style:str='normal'):
    colors_DB, styles_DB = get_colors_styles()
    art_string:str = text2art(title, font=font)
    art_string_colored = last_color = before_last_color = ''
    for ch in art_string:
        if ch.strip():
            while True:
                current_color:str = random.choice(tuple(colors_DB.keys()))
                if (
                    current_color != last_color and 
                    current_color != before_last_color
                ):
                    art_string_colored += colorize(ch, current_color, style)
                    before_last_color:str = last_color
                    last_color:str = current_color
                    break
        else:
            art_string_colored += ch
    
    return art_string_colored.rstrip()

def text_to_box(text:str, box_line:str='-'):
    boxed_text:str = (
        f'{box_line*(len(text)+2)}\n|{text}|\n{box_line*(len(text)+2)}'
    )

    return boxed_text