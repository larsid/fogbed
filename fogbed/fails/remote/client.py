from typing import Any, Dict, List, Optional

import httpx

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.fails.events import FailEvent
from fogbed.fails.plan import FailPlan, NodeSpec


class FailWorkerClient:
    def __init__(self, url: str, client: Optional[httpx.Client] = None, timeout: float = 30.0):
        self.url    = url.rstrip('/')
        self.client = client if(client is not None) else httpx.Client(timeout=timeout)

    def load_plan(self, plan: FailPlan):
        self._request('POST', '/fails', plan.to_dict())

    def start(self, start_at: Optional[float] = None):
        body = {} if(start_at is None) else {'start_at': start_at}
        self._request('POST', '/fails/start', body)

    def stop(self):
        self._request('POST', '/fails/stop', timeout=None)

    def status(self) -> Dict[str, Any]:
        return self._request('GET', '/fails/status')['content']

    def events(self) -> List[FailEvent]:
        return [FailEvent.from_dict(event) for event in self._request('GET', '/fails/events')['content']]

    def fail_node(self, name: str, mode: str, spec: Optional[NodeSpec] = None) -> bool:
        body: Dict[str, Any] = {'mode': mode}
        if(spec is not None):
            body['spec'] = spec.to_dict()
        return self._request_change('POST', f'/containers/{name}/fail', body)

    def recover_node(self, name: str) -> bool:
        return self._request_change('POST', f'/containers/{name}/recover')

    def close(self):
        self.client.close()

    def _request_change(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> bool:
        response = self._send(method, path, body)
        if(response.status_code == 409):
            return False
        self._verify(response)
        return True

    def _request(self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        timeout: Any = httpx.USE_CLIENT_DEFAULT
    ) -> Dict[str, Any]:
        response = self._send(method, path, body, timeout)
        return self._verify(response)

    def _send(self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]],
        timeout: Any = httpx.USE_CLIENT_DEFAULT
    ) -> httpx.Response:
        try:
            return self.client.request(method, f'{self.url}{path}', json=body, timeout=timeout)
        except httpx.HTTPError as ex:
            raise FailInjectionError(f'{self.url}: {ex}')

    def _verify(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            data = {'error': response.text}

        if(response.status_code == 404):
            raise ContainerNotFound(f'{self.url}: {data.get("error")}')
        if(response.is_error):
            raise FailInjectionError(f'{self.url}: {data.get("error")}')
        return data
