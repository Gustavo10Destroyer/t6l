import time
import socket
from typing import Any, Dict, List
from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

class _Listener(ServiceListener):
    def __init__(self) -> None:
        self.services: Dict[str, ServiceInfo] = {}

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            self.services[name] = info

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.services.pop(name, None)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            self.services[name] = info

def discover(
    service_type: str,
    timeout: float = 3.0,
) -> List[ServiceInfo]:
    zeroconf = Zeroconf()
    listener = _Listener()
    ServiceBrowser(zeroconf, service_type, listener)

    time.sleep(timeout)
    zeroconf.close()

    return list(listener.services.values())

def resolve_service(info: ServiceInfo) -> Dict[str, object]:
    '''
    Extrai dados úteis do ServiceInfo.
    '''
    addresses = [
        socket.inet_ntoa(addr)
        for addr in info.addresses
    ]

    return {
        'name': info.name,
        'host': info.server,
        'port': info.port,
        'addresses': addresses,
        'properties': {
            k.decode(): v.decode() if v is not None else v
            for k, v in info.properties.items()
        },
    }


def discover_resolved(
    service_type: str,
    timeout: float = 3.0,
) -> List[Dict[str, Any]]:
    '''
    Descobre e já retorna os serviços resolvidos.
    '''
    infos = discover(service_type, timeout)
    return [resolve_service(info) for info in infos]

def get_discovered_server(name: str, servers: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    for server in servers:
        properties: Dict[str, Any] = server.get('properties', {})
        if properties.get('name', '') == name:
            return server

def main():
    servers = discover_resolved('_d3str0yer._tcp.local.')
    print(servers)

if __name__ == '__main__':
    main()