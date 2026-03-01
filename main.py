import sys
sys.dont_write_bytecode = True

import argparse
import subprocess
from api import API
from pathlib import Path
from typing import Any, Dict, List
from setup import setup_tool, remove_tool
from service_discovery import discover_resolved, get_discovered_server
from t6server import T6Server, load_servers, get_server, register_server, remove_server

BASE_DIR = Path(__file__).resolve().parent if not getattr(sys, 'frozen', False) else Path(sys.executable).resolve().parent

def main() -> None:
    parser = argparse.ArgumentParser(
        prog='t6l',
        epilog='T6 Server Launcher v1.0.0',
        description='A CLI tool to launch, watch and manage Plutonium T6 servers'
    )
    parser.add_argument('-v', '--version', action='version', version='T6 Server Launcher v1.0.0 (https://github.com/gustavo10destroyer/t6l)')

    subparsers = parser.add_subparsers(dest='command', required=True)

    create_parser = subparsers.add_parser('create', description='Cria um perfil de um servidor')
    create_parser.add_argument('name', help='O nome de exibição do perfil')
    create_parser.add_argument('--key', help='A chave do servidor', required=True)
    create_parser.add_argument('--mod', help='O mod que o servidor deve carregar', default='')
    create_parser.add_argument('--game', help='O diretório do jogo', required=True)
    create_parser.add_argument('--home', help='O caminho até a pasta Plutonium do servidor', required=True)
    create_parser.add_argument('--port', type=int, help='A porta que o servidor vai escutar', required=True)
    create_parser.add_argument('--rcon', help='A senha para o Remote Console', required=True)
    create_parser.add_argument('--config-file', help='O arquivo de configuração que o servidor deve executar ao iniciar', required=True)

    list_parser = subparsers.add_parser('list', description='Lista todos os perfis de servidores')
    list_parser.add_argument('-a', '--all', dest='show_all', action='store_true', help='Mostrar tudo')

    edit_parser = subparsers.add_parser('edit', description='Edita um perfil existente')
    edit_parser.add_argument('server', help='O nome atual do servidor')
    edit_parser.add_argument('--key', help='Atualiza a chave do servidor')
    edit_parser.add_argument('--mod', help='Atualiza o mod do servidor')
    edit_parser.add_argument('--game', help='Atualiza o diretório do jogo usado pelo servidor')
    edit_parser.add_argument('--home', help='Atualiza a HOME do servidor')
    edit_parser.add_argument('--name', help='Atualiza o nome do servidor')
    edit_parser.add_argument('--port', type=int, help='Atualiza a porta do servidor')
    edit_parser.add_argument('--rcon', help='Atualiza a senha para o Remote Console(RCON)')
    edit_parser.add_argument('--config-file', help='Atualiza o arquivo de configuração do servidor')

    delete_parser = subparsers.add_parser('delete', description='Apaga um perfil existente')
    delete_parser.add_argument('server', help='O nome atual do servidor')

    subparsers.add_parser('servers', description='Mostra a lista de servidores em execução')

    start_parser = subparsers.add_parser('start', description='Inicia um servidor T6 a partir de um perfil')
    start_parser.add_argument('server', help='O nome do servidor')
    start_parser.add_argument('--hidden', action='store_true', help='Impede que o servidor crie uma janela')

    stop_parser = subparsers.add_parser('stop', description='Para um servidor T6 a partir do perfil')
    stop_parser.add_argument('server', help='O nome do servidor')
    stop_parser.add_argument('--keep-bootstrapper', action='store_true', help='Para o servidor mas deixa o bootstrapper aberto (a API do servidor continua funcionando)')

    setup_parser = subparsers.add_parser('setup', description='Configura a ferramenta no ambiente')
    setup_parser.add_argument('--remove', action='store_true', help='Remove a ferramenta do ambiente')

    args = parser.parse_args()
    if args.command == 'create':
        register_server(
            T6Server(
                args.key,
                args.mod,
                args.game,
                args.home,
                args.name,
                args.port,
                args.rcon,
                args.config_file
            )
        )
        return

    if args.command == 'list':
        servers = load_servers()
        if len(servers) == 0:
            print('Não há nenhum perfil configurado ainda.')
            return

        for server in servers:
            print(f'--- Servidor {server.name} ---')
            print(f'HOME: "{server.home}"')
            if args.show_all:
                print(f'Mod: {server.mod}')
                print(f'Chave: {server.key}')
                print(f'Senha RCON: {server.rcon}')
                print(f'Diretório do jogo: "{server.home}"')
            print(f'Porta: {server.port}')
            print(f'Arquivo de configuração: {server.config_file}')

    if args.command == 'edit':
        server = get_server(args.server)
        if server is None:
            print(f'Nenhum servidor nomeado como {args.server} foi encontrado.')
            return

        if args.name is not None:
            server.name = args.name

        if args.port is not None:
            server.port = args.port

        if args.game is not None:
            server.game = args.game

        if args.home is not None:
            server.home = args.home

        if args.rcon is not None:
            server.rcon = args.rcon

        if args.key is not None:
            server.key = args.key

        if args.mod is not None:
            server.mod = args.mod

        remove_server(args.server)
        register_server(server)
        print(f'O servidor {args.server} foi atualizado com sucesso!')

    if args.command == 'delete':
        server = get_server(args.server)
        if server is None:
            print(f'Nenhum servidor nomeado como {args.server} foi encontrado.')
            return

        try:
            answer = input(f'Você tem certeza que deseja apagar o servidor {server.name}? (s/N): ')
            answer = answer.lower()
        except KeyboardInterrupt:
            return

        if answer != 'y' and answer != 's' and answer != 'yes' and answer != 'sim':
            print('Ação cancelada.')
            return

        remove_server(server)
        print(f'O servidor {server.name} foi apagado.')
        return
    
    if args.command == 'servers':
        servers = discover_resolved('_d3str0yer._tcp.local.')
        if len(servers) == 0:
            print('Nenhum servidor foi encontrado.')
            return

        for server in servers:
            properties: Dict[str, Any] = server.get('properties', {})
            type_ = properties.get('type')
            if type_ is None or type_ != 't6server':
                continue

            addresses = server.get('addresses', [])
            if len(addresses) < 1:
                continue

            name: str = properties.get('name', '')
            host: str = addresses[0]
            port: int = server.get('port', 0)
            token: str = properties.get('authorization', '')
            print(f'Servidor: {name}')
            print(f'Endereço: http://{host}:{port}')
            print(f'Autorização: Bearer {token}')

        return

    if args.command == 'start':
        server_name: str = args.server
        servers = discover_resolved('_d3str0yer._tcp.local.')
        server = get_discovered_server(server_name, servers)
        if server is not None:
            addresses: List[str] = server.get('addresses', [])
            if len(addresses) < 1:
                print('O bootstrapper encontrado está com problemas. Tente reiniciar o dispositivo.')
                return

            host: str = addresses[0]
            port: int = server.get('port', 0)
            properties: Dict[str, Any] = server.get('properties', {})
            authorization: str = properties.get('authorization', '')
            api = API(host, port, authorization)

            remote_status_response = api.get_status()
            if remote_status_response is None:
                print('Falha ao consultar o estado do bootstrapper. A porta está correta?')
                return
            
            if remote_status_response.status == 'stopped':
                print('Iniciando o servidor...')
                remote_start_response = api.start()
                if remote_start_response is None:
                    print('Falha ao iniciar o servidor. Tente novamente')
                    return

                if remote_start_response.success == False:
                    print(f'Falha ao iniciar o servidor: {remote_start_response.message}')
                    return

                print('O servidor foi iniciado!')
                return

            print(f'O servidor {server_name} já está em execução.')
            return

        bootstrapper = str(BASE_DIR / 'bootstrapper.py')
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        subprocess.Popen(
            [
                sys.executable,
                bootstrapper,
                server_name,
                str(args.hidden)
            ],
            cwd=BASE_DIR,
            # stdin=subprocess.DEVNULL,
            # stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
            close_fds=True,
            startupinfo=startupinfo,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
            start_new_session=True
        )
        print('O servidor(bootstrapper) foi iniciado.')
        return

    if args.command == 'stop':
        server_name: str = args.server
        servers = discover_resolved('_d3str0yer._tcp.local.')
        server = get_discovered_server(server_name, servers)
        if server is None:
            print(f'Nenhum servidor chamado {server_name} foi encontrado. Verifique a lista de servidores em execução usando o comando "t6l servers"')
            return

        addresses: List[str] = server.get('addresses', [])
        if len(addresses) < 1:
            print('O bootstrapper encontrado está com problemas. Tente reiniciar o dispositivo.')
            return

        host: str = addresses[0]
        port: int = server.get('port', 0)
        properties: Dict[str, Any] = server.get('properties', {})
        authorization: str = properties.get('authorization', '')
        api = API(host, port, authorization)

        remote_status_response = api.get_status()
        if remote_status_response is None:
            print('Falha ao obter o estado do servidor')
            return

        if args.keep_bootstrapper and remote_status_response.status == 'stopped':
            print('O servidor está parado')
            return

        if args.keep_bootstrapper:
            remote_stop_response = api.stop()
            if remote_stop_response is None:
                print('Falha ao parar o servidor. Tente novamente')
                return

            if remote_stop_response.success == False:
                print('Falha ao parar o servidor.')
                return

            print('O servidor foi parado.')
            return
        
        remote_quit_response = api.quit()
        if remote_quit_response is None:
            print('Falha ao parar o servidor. Tente novamente')
            return

        if remote_quit_response.success == False:
            print(f'Falha ao parar o servidor: {remote_quit_response.message}')
            return

        print('O servidor foi parado.')
        return

    if args.command == 'setup':
        if args.remove:
            remove_tool()
            return

        setup_tool()

if __name__ == '__main__':
    main()