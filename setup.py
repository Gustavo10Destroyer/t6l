import os
import sys

class Colors:
    RED = '\x1b[31m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    RESET = '\x1b[0m'

def setup_tool():
    file_path = os.path.expandvars('$localappdata\\Microsoft\\WindowsApps\\t6l.cmd')
    if os.path.isfile(file_path):
        message = 'A ferramenta já está no seu ambiente, use %s para obter ajuda.'
        print(f'[{Colors.GREEN}INFO{Colors.RESET}] {message % f'{Colors.YELLOW}t6l --help{Colors.RESET}'}')
        return

    with open(file_path, 'wb') as file:
        file.write(f'@echo off\nchcp 65001 >nul\n"{sys.executable}" "{os.path.normpath(os.path.abspath(sys.argv[0]))}" %*'.encode('utf-8'))

    message = 'A ferramenta foi adicionada ao seu ambiente. Use %s para saber mais.'
    print(f'[{Colors.GREEN}INFO{Colors.RESET}] {message % f'{Colors.YELLOW}t6l --help{Colors.RESET}'}')

def remove_tool():
    file_path = os.path.expandvars('$localappdata\\Microsoft\\WindowsApps\\t6l.cmd')
    if not os.path.isfile(file_path):
        message = 'A ferramenta não está instalada.'
        print(f'[{Colors.RED}ERR!{Colors.RESET}] {message}')
        sys.exit(1)

    os.unlink(file_path)
    message = 'A ferramenta foi removida do seu ambiente.'
    print(f'[{Colors.GREEN}INFO{Colors.RESET}] {message}')