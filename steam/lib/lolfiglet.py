import subprocess
import time
import os
import random
import sys


def lolfiglet(message, fontname=None, duration=10, delay=0.025):
    if fontname is None:
        fonts = os.listdir(os.path.expanduser("~/.local/share/figlet/"))
        fontname = os.path.basename(random.choice(fonts))

    font = f"~/.local/share/figlet/{fontname}"

    ret = subprocess.run(
        f'figlet -ktc "{message}" -f {font}',
        capture_output=True,
        shell=True,
    )

    height = ret.stdout.count(b'\n')
    num = int(duration / delay)

    try:
        subprocess.run("tput civis", shell=True)
        for i in range(num):
            subprocess.run(f'figlet -ktc "{message}" -f {font} | lolcat -o {i}', shell=True)
            print("\033[A"*height, end='')
            sys.stdout.flush()
            time.sleep(delay)
    finally:
        print("\033[B"*height, end='')
        subprocess.run("tput cnorm", shell=True)
