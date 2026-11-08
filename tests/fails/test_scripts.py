import sys

from fogbed import scripts


def test_worker_command_serves_fail_routes(monkeypatch):
    commands = []
    monkeypatch.setattr(scripts, 'run_command', commands.append)

    scripts.run_worker(port=5001)

    assert commands == [['sudo', sys.executable, '-m', 'fogbed.fails.remote.server', '-p=5001']]
