from __future__ import annotations

import logging
import signal
import time

from src.browser_agent.service import fail_stale_browser_agent_runs, run_browser_agent_worker_once
from src.db.session import get_session_factory
from src.shared.config.settings import get_settings

logger = logging.getLogger(__name__)


class BrowserAgentWorkerService:
	"""Long-lived browser-agent worker loop for ECS or other process supervisors."""

	def __init__(self) -> None:
		self._stop_requested = False

	def request_stop(self) -> None:
		self._stop_requested = True

	def install_signal_handlers(self) -> None:
		def _handle_signal(signum: int, _frame: object) -> None:
			logger.info('browser_agent_worker_signal_received signum=%s', signum)
			self.request_stop()

		signal.signal(signal.SIGTERM, _handle_signal)
		signal.signal(signal.SIGINT, _handle_signal)

	def run_forever(self) -> None:
		settings = get_settings()
		session_factory = get_session_factory()

		logger.info(
			'browser_agent_worker_start poll_seconds=%s stale_heartbeat_seconds=%s',
			settings.browser_agent_worker_poll_seconds,
			settings.browser_agent_worker_stale_heartbeat_seconds,
		)

		while not self._stop_requested:
			with session_factory() as session:
				recovered = fail_stale_browser_agent_runs(session, settings=settings)
				session.commit()
				if recovered:
					logger.warning('browser_agent_worker_recovered_stale_runs count=%s', recovered)

			result = run_browser_agent_worker_once(settings=settings)
			if result is None:
				time.sleep(settings.browser_agent_worker_poll_seconds)
				continue

			logger.info(
				'browser_agent_worker_processed_run run_id=%s status=%s',
				result.id,
				result.status,
			)

		logger.info('browser_agent_worker_stop_requested')


def main() -> None:
	service = BrowserAgentWorkerService()
	service.install_signal_handlers()
	service.run_forever()


if __name__ == '__main__':
	main()
