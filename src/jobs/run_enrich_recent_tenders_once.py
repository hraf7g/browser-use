from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.jobs.enrich_recent_tenders_job_service import run_enrich_recent_tenders_job


def main() -> None:
	"""
	Execute the recent-tender AI enrichment job once from environment input.

	Current behavior:
		- Enrich tenders updated in the last 24 hours.
		- Print a compact deterministic summary for operators.
	"""
	since = datetime.now(UTC) - timedelta(days=1)
	result = run_enrich_recent_tenders_job(since=since)
	print(f'run_enrich_recent_tenders_once_since={since.isoformat()}')
	print(f'run_enrich_recent_tenders_once_attempted_count={result.attempted_count}')
	print(f'run_enrich_recent_tenders_once_enriched_count={result.enriched_count}')
	print(f'run_enrich_recent_tenders_once_failed_count={result.failed_count}')
	print(f'run_enrich_recent_tenders_once_skipped_count={result.skipped_count}')


if __name__ == '__main__':
	main()
