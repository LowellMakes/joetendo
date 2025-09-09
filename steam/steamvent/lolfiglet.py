import subprocess
import time
import os
import random
import sys


def lolfiglet(message, font=None, duration=10, delay=0.025):
    if font is None:
        fonts = os.listdir(os.path.expanduser("/usr/share/figlet/"))
        fonts = [f for f in fonts if f.endswith(".flf")]
        font = os.path.basename(random.choice(fonts))

    ret = subprocess.run(
        f'figlet -ktc "{message}" -f {font}',
        capture_output=True,
        shell=True,
    )

    term_x, term_y = os.get_terminal_size()
    height = ret.stdout.count(b'\n')

    y_margin = term_y - height
    y_offset = int(y_margin / 2)

    num = int(duration / delay)

    try:
        subprocess.run("tput civis", shell=True)
        print("\n" * y_offset, end='')
        for i in range(num):
            subprocess.run(f'figlet -ktc "{message}" -f {font} | lolcat -o {i}', shell=True)
            print("\033[A"*height, end='')
            sys.stdout.flush()
            time.sleep(delay)
    finally:
        print("\033[B"*height, end='')
        subprocess.run("tput cnorm", shell=True)
