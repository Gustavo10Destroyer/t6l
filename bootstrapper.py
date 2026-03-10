from socketserver import BaseServer
import sys
sys.dont_write_bytecode = True

import os
import json
import socket
import psutil
import logging
import subprocess
from uuid import uuid4
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from zeroconf import Zeroconf, ServiceInfo

from rcon import is_alive
from time import time, sleep
from typing import Any, Dict, Tuple
from t6server import T6Server, get_server

rcon_poll_rate = 30 # seconds

logger: logging.Logger | None = None

def kill_process_tree(parent: psutil.Process):
    childs = parent.children(recursive=True)

    for child in childs:
        child.kill()

    parent.kill()

class ServerNode:
    def __init__(
        self,
        server: T6Server,
        hidden: bool
    ):
        self.hidden = hidden
        self.server = server
        self.process: subprocess.Popen[bytes] | None = None

    def start(self):
        if self.process is not None and self.process.poll() is None:
            return

        if self.hidden:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                [
                    os.path.join(self.server.home, 'bin', 'plutonium-bootstrapper-win32.exe'),
                    't6zm', f'{self.server.game}',
                    '+set', 'key', self.server.key,
                    '+set', 'fs_game', self.server.mod,
                    '+set', 'net_port', str(self.server.port),
                    '+set', 'sv_hostname', self.server.name,
                    '+exec', self.server.config_file,
                    '-dedicated', '+map_rotate'
                ],
                cwd=self.server.home,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return

        self.process = subprocess.Popen(
            [
                os.path.join(self.server.home, 'bin', 'plutonium-bootstrapper-win32.exe'),
                't6zm' if self.server.type == 'zm' else 't6mp', # t6zm or t6mp
                f'{self.server.game}',
                '+set', 'key', self.server.key,
                '+set', 'fs_game', self.server.mod,
                '+set', 'net_port', str(self.server.port),
                '+set', 'sv_hostname', self.server.name,
                '+exec', self.server.config_file,
                '-dedicated', '+map_rotate'
            ],
            cwd=self.server.home,
            shell=True
        )

    def stop(self):
        if self.process is None or self.process.poll() is not None:
            return

        kill_process_tree(psutil.Process(self.process.pid))

    def status(self):
        if self.process is None or self.process.poll() is not None:
            return 'stopped'

        return 'running'

def create_http_server(node: ServerNode) -> Tuple[HTTPServer, str]:
    token = str(uuid4())

    class Handler(BaseHTTPRequestHandler):
        def __init__(self, request: socket.socket | tuple[bytes, socket.socket], client_address: Any, server: BaseServer) -> None:
            super().__init__(request, client_address, server)

        def do_GET(self):
            if self.path == '/api/v1/status':
                self.respond(200, {
                    'success': True,
                    'message': 'ok',
                    'status': node.status()
                })
            else:
                self.respond(404, {
                    'success': False,
                    'message': 'not found'
                })

        def is_authorized(self) -> bool:
            nonlocal token

            auth = self.headers.get('authorization')
            if auth is None:
                return False

            if not auth.startswith('Bearer '):
                return False

            _token = auth[7:]
            if _token != token:
                return False

            return True

        def do_POST(self):
            if self.path == '/api/v1/quit':
                if not self.is_authorized():
                    self.respond(403, {
                        'success': False,
                        'message': 'unauthorized'
                    })
                    return

                self.respond(200, {
                    'success': True,
                    'message': 'the server is closing'
                })

                node.stop()
                sys.exit(0)
            if self.path == '/api/v1/start':
                if not self.is_authorized():
                    self.respond(403, {
                        'success': False,
                        'message': 'unauthorized'
                    })
                    return

                if node.status() != 'stopped':
                    self.respond(400, {
                        'success': False,
                        'message': 'already running'
                    })
                    return

                node.start()

                self.respond(200, {
                    'success': True,
                    'message': 'started'
                })
            elif self.path == '/api/v1/stop':
                if not self.is_authorized():
                    self.respond(403, {
                        'success': False,
                        'message': 'unauthorized'
                    })
                    return

                node.stop()
                self.respond(200, {
                    'success': True,
                    'message': 'stopped'
                })
            else:
                self.respond(404, {
                    'success': False,
                    'message': 'not found',
                })

        def respond(self, code: int, obj: Dict[str, Any]):
            self.send_response(code)
            self.send_header('content-type', 'application/json; charset=UTF-8')
            self.end_headers()
            self.wfile.write(json.dumps(obj).encode('utf-8'))

        def log_message(self, format: str, *args: Any) -> None:
            # return super().log_message(format, *args)
            return

    httpd = HTTPServer(('0.0.0.0', 0), Handler)
    return httpd, token

def announce_service(name: str, port: int, token: str):
    zeroconf = Zeroconf()

    # pega IP real da interface ativa
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    s.close()

    info = ServiceInfo(
        '_d3str0yer._tcp.local.',
        f'{name}._d3str0yer._tcp.local.',
        addresses=[socket.inet_aton(ip)],
        port=port,
        properties={'name': name, 'type': 't6server', 'authorization': token},
    )

    print(f'Anúncio criado em {ip}:{port}')

    zeroconf.register_service(info)
    return zeroconf, info

def watch_server_status(node: ServerNode, logger: logging.Logger):
    global rcon_poll_rate

    last_check = time() + 60
    while True:
        sleep(1)

        if node.status() == 'stopped': continue
        if (time() - last_check) < rcon_poll_rate: continue

        last_check = time()
        if not is_alive('127.0.0.1', node.server.port):
            logger.warning(f'O servidor {node.server.name} não está respondendo, reiniciando...')
            node.stop()
            sleep(2)
            node.start()

def main():
    if len(sys.argv) < 2:
        print('Informe o nome do perfil para iniciar!')
        return

    hidden = False
    if len(sys.argv) >= 3:
        hidden = sys.argv[2].lower() == 'true'

    server_name = sys.argv[1]
    server = get_server(server_name)
    if server is None:
        print(f'Nenhum perfil chamado {server_name} foi encontrado.')
        return

    logger = logging.getLogger(f'bootstrapper.{server.name}')

    node = ServerNode(server, hidden)
    node.start()
    Thread(
        target=watch_server_status,
        args=[node, logger],
        daemon=True
    ).start()

    httpd, token = create_http_server(node)
    port = httpd.server_address[1]

    zeroconf, info = announce_service(node.server.name, port, token)

    try:
        print('O bootstrapper está em execução.')
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\rEncerrando o servidor HTTP...')
        httpd.shutdown()
        print('Parando o servidor do jogo...')
        node.stop()
    finally:
        zeroconf.unregister_service(info)
        zeroconf.close()

if __name__ == '__main__':
    main()