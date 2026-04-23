from __future__ import annotations

from src.browser_agent.service import run_browser_agent_worker_once


def main() -> None:
	"""Execute one claimed browser-agent run if any are queued."""
	result = run_browser_agent_worker_once()
	if result is None:
		print('run_browser_agent_worker_once_status=idle')
		return
	print(f'run_browser_agent_worker_once_status={result.status}')
	print(f'run_browser_agent_worker_once_run_id={result.id}')


if __name__ == '__main__':
	main()
