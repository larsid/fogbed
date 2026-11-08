import socket
from typing import Any, Callable, Dict

from flask import Blueprint, jsonify, request

from clusternet.apis.presentation.exceptions import BadRequestException
from clusternet.apis.presentation.helpers import (
    bad_request, created, error, internal_server_error, not_found, parse_request, success, validate_required_params
)
from clusternet.apis.presentation.protocols import Controller, HttpRequest, HttpResponse

from fogbed.exceptions import ContainerNotFound, FailInjectionError
from fogbed.fails.agent import FailAgent
from fogbed.fails.plan import FailPlan, NodeSpec

from mininet.log import info


def conflict(body: Dict[str, Any]) -> HttpResponse:
    return HttpResponse(status_code=409, body=body)


def get_hostname() -> str:
    return socket.gethostname()


class LoadFailPlanController(Controller):
    def __init__(self, agent: FailAgent) -> None:
        self.agent = agent

    def handle(self, request: HttpRequest) -> HttpResponse:
        hostname = get_hostname()

        try:
            plan = FailPlan.from_dict(request.body)
            self.agent.load(plan)
            return created({'content': f'[{hostname}]: fail plan registered with {len(plan.targets)} targets'})

        except ValueError as ex:
            return bad_request(error(f'[{hostname}]: {ex}'))
        except FailInjectionError as ex:
            return conflict(error(f'[{hostname}]: {ex}'))
        except Exception as ex:
            return internal_server_error(error(f'[{hostname}]: {ex}'))


class StartFailsController(Controller):
    def __init__(self, agent: FailAgent) -> None:
        self.agent = agent

    def handle(self, request: HttpRequest) -> HttpResponse:
        hostname = get_hostname()

        try:
            start_at = request.get('start_at')
            self.agent.start(None if(start_at is None) else float(start_at))
            return success({'content': f'[{hostname}]: fails scheduled to {self.agent.started_at}'})

        except (TypeError, ValueError) as ex:
            return bad_request(error(f'[{hostname}]: invalid start_at: {ex}'))
        except FailInjectionError as ex:
            return conflict(error(f'[{hostname}]: {ex}'))
        except Exception as ex:
            return internal_server_error(error(f'[{hostname}]: {ex}'))


class StopFailsController(Controller):
    def __init__(self, agent: FailAgent) -> None:
        self.agent = agent

    def handle(self, request: HttpRequest) -> HttpResponse:
        hostname = get_hostname()

        try:
            self.agent.stop()
            return success({'content': f'[{hostname}]: fails stopped and nodes restored'})

        except Exception as ex:
            return internal_server_error(error(f'[{hostname}]: {ex}'))


class GetFailStatusController(Controller):
    def __init__(self, agent: FailAgent) -> None:
        self.agent = agent

    def handle(self, request: HttpRequest) -> HttpResponse:
        try:
            return success({'content': self.agent.status()})
        except Exception as ex:
            return internal_server_error(error(f'[{get_hostname()}]: {ex}'))


class GetFailEventsController(Controller):
    def __init__(self, agent: FailAgent) -> None:
        self.agent = agent

    def handle(self, request: HttpRequest) -> HttpResponse:
        try:
            return success({'content': [event.to_dict() for event in self.agent.events()]})
        except Exception as ex:
            return internal_server_error(error(f'[{get_hostname()}]: {ex}'))


class FailContainerController(Controller):
    def __init__(self, agent: FailAgent, name: str) -> None:
        self.agent = agent
        self.name  = name

    def handle(self, request: HttpRequest) -> HttpResponse:
        hostname = get_hostname()

        try:
            validate_required_params(request, ['mode'])
            mode = str(request.body['mode'])
            spec = request.get('spec')
            node = None if(spec is None) else NodeSpec.from_dict(spec)

            if(not self.agent.fail_node(self.name, mode, spec=node)):
                return conflict(error(f'[{hostname}]: container {self.name} is already failed'))

            return success({'content': f'[{hostname}]: container {self.name} failed by {mode}'})

        except (BadRequestException, ValueError, KeyError, TypeError, AttributeError) as ex:
            return bad_request(error(f'[{hostname}]: {ex}'))
        except ContainerNotFound as ex:
            return not_found(error(f'[{hostname}]: {ex}'))
        except Exception as ex:
            return internal_server_error(error(f'[{hostname}]: {ex}'))


class RecoverContainerController(Controller):
    def __init__(self, agent: FailAgent, name: str) -> None:
        self.agent = agent
        self.name  = name

    def handle(self, request: HttpRequest) -> HttpResponse:
        hostname = get_hostname()

        try:
            if(not self.agent.recover_node(self.name)):
                return conflict(error(f'[{hostname}]: container {self.name} is not failed'))

            return success({'content': f'[{hostname}]: container {self.name} recovered'})

        except ContainerNotFound as ex:
            return not_found(error(f'[{hostname}]: {ex}'))
        except Exception as ex:
            return internal_server_error(error(f'[{hostname}]: {ex}'))


def create_fails_blueprint(agent_provider: Callable[[], FailAgent]) -> Blueprint:
    blueprint = Blueprint('fails', __name__)

    def make_response(controller: Controller):
        response = controller.handle(parse_request(request))
        return jsonify(response.body), response.status_code

    @blueprint.before_app_request
    def stop_fails_with_worker():
        if(request.path != '/stop'):
            return

        try:
            agent_provider().stop()
        except FailInjectionError as ex:
            info(f'*** [{get_hostname()}]: {ex}\n')

    @blueprint.route('/fails', methods=['POST'])
    def load_fail_plan():
        return make_response(LoadFailPlanController(agent_provider()))

    @blueprint.route('/fails/start', methods=['POST'])
    def start_fails():
        return make_response(StartFailsController(agent_provider()))

    @blueprint.route('/fails/stop', methods=['POST'])
    def stop_fails():
        return make_response(StopFailsController(agent_provider()))

    @blueprint.route('/fails/status', methods=['GET'])
    def get_fail_status():
        return make_response(GetFailStatusController(agent_provider()))

    @blueprint.route('/fails/events', methods=['GET'])
    def get_fail_events():
        return make_response(GetFailEventsController(agent_provider()))

    @blueprint.route('/containers/<string:name>/fail', methods=['POST'])
    def fail_container(name: str):
        return make_response(FailContainerController(agent_provider(), name))

    @blueprint.route('/containers/<string:name>/recover', methods=['POST'])
    def recover_container(name: str):
        return make_response(RecoverContainerController(agent_provider(), name))

    return blueprint
