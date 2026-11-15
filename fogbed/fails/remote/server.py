import argparse
import os

from flask import Flask

from clusternet.apis.worker.data import WorkerInstance
from clusternet.server.worker_app import server

from fogbed.fails.agent import FailAgent
from fogbed.fails.operators import ContainernetOperator
from fogbed.fails.remote.routes import create_fails_blueprint, get_hostname


def create_worker_app() -> Flask:
    if('fails' not in server.blueprints):
        agent = FailAgent(ContainernetOperator(WorkerInstance.instance), source=get_hostname())
        server.register_blueprint(create_fails_blueprint(lambda: agent))
    return server


def main():
    parser = argparse.ArgumentParser('sudo fogbed worker')
    parser.add_argument('-p', '--port', type=int, default=5000, help='run server on especified port (default: 5000)')
    args = parser.parse_args()

    create_worker_app().run(host='0.0.0.0', port=int(os.environ.get('PORT', args.port)))

if(__name__=='__main__'):
    main()
