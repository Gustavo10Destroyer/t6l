import requests
from dataclasses import dataclass
from requests.exceptions import (
    Timeout,
    HTTPError,
    ConnectionError,
    JSONDecodeError
)

from typing import Any, Dict, Union

@dataclass
class APIResponse:
    message: str
    success: bool

@dataclass
class APIStatusResponse(APIResponse):
    status: str

class API:
    def __init__(
        self,
        host: str,
        port: int,
        authorization: str
    ):
        self.host = host
        self.port = port
        self.authorization = authorization

    def start(self) -> Union[APIResponse, None]:
        try:
            response = requests.post(f'http://{self.host}:{self.port}/api/v1/start', headers={
                'authorization': f'Bearer {self.authorization}'
            })
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
        except (Timeout, HTTPError, ConnectionError, JSONDecodeError):
            return

        return APIResponse(
            data.get('message', ''),
            data.get('success', False),
        )

    def stop(self) -> Union[APIResponse, None]:
        try:
            response = requests.post(f'http://{self.host}:{self.port}/api/v1/stop', headers={
                'authorization': f'Bearer {self.authorization}'
            })
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
        except (Timeout, HTTPError, ConnectionError, JSONDecodeError):
            return

        return APIResponse(
            data.get('message', ''),
            data.get('success', False),
        )

    def quit(self) -> Union[APIResponse, None]:
        try:
            response = requests.post(f'http://{self.host}:{self.port}/api/v1/quit', headers={
                'authorization': f'Bearer {self.authorization}'
            })
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
        except (Timeout, HTTPError, ConnectionError, JSONDecodeError):
            return

        return APIResponse(
            data.get('message', ''),
            data.get('success', False),
        )

    def get_status(self) -> Union[APIStatusResponse, None]:
        try:
            response = requests.get(f'http://{self.host}:{self.port}/api/v1/status')
            response.raise_for_status()
            data: Dict[str, Any] = response.json()
        except (Timeout, HTTPError, ConnectionError, JSONDecodeError):
            return

        return APIStatusResponse(
            data.get('message', ''),
            data.get('success', False),
            data.get('status', ''),
        )