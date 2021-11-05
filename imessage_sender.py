import os
import subprocess
from shlex import quote


def send(number, message):
    # Get path to apple script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    relative_path = 'osascript/sendMessage.applescript'
    path = f'{dir_path}/{relative_path}'

    #  Execute apple script to send text message
    cmd = f'osascript {path} {quote(number)} {quote(message)}'
    subprocess.call(cmd, shell=True)
