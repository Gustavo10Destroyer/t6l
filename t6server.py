import sys
sys.dont_write_bytecode = True

import os
import json
from pathlib import Path
from typing import Any, Dict, List
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent if not getattr(sys, 'frozen', False) else Path(sys.executable).resolve().parent

@dataclass
class T6Server:
    key: str
    mod: str
    game: str
    home: str
    name: str
    port: int
    rcon: str
    config_file: str

    def __repr__(self) -> str:
        return '\r\x1b[2KT6Server("%s") {\n    home: "%s",\n    port: %i\n}' % (self.name, self.home, self.port)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'mod': self.mod,
            'game': self.game,
            'home': self.home,
            'name': self.name,
            'port': self.port,
            'rcon': self.rcon,
            'config_file': self.config_file
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            data.get('key', ''),
            data.get('mod', ''),
            data.get('game', ''),
            data.get('home', ''),
            data.get('name', ''),
            data.get('port', 0),
            data.get('rcon', ''),
            data.get('config_file', '')
        )

def load_servers() -> List[T6Server]:
    if not os.path.exists(BASE_DIR / 'servers.json'):
        return []

    with open(BASE_DIR / 'servers.json', 'r', encoding='utf-8') as file:
        return [T6Server.from_dict(s) for s in json.load(file)]

def save_servers(servers: List[T6Server]):
    with open(BASE_DIR / 'servers.json', 'w', encoding='utf-8') as file:
        json.dump([s.to_dict() for s in servers], file, ensure_ascii=False, indent=4)

def get_server(name: str) -> T6Server | None:
    servers = load_servers()
    for server in servers:
        if server.name == name:
            return server

def remove_server(server: str | T6Server):
    servers = load_servers()
    name = server.name if isinstance(server, T6Server) else server
    for server in list(servers):
        if server.name == name:
            servers.remove(server)

    save_servers(servers)

def register_server(server: T6Server):
    servers = load_servers()

    for _server in servers:
        if _server.name == server.name:
            print('Os nomes não podem se repetir!')
            return

    servers.append(server)
    save_servers(servers)