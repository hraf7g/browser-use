from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from browser_use.llm.messages import SystemMessage, UserMessage
from src.ai.factory import AIRuntimeDependencyError, build_ai_runtime
from src.ai.usage_budget_service import estimate_bedrock_converse_input_tokens
from src.db.session import get_session_factory
from src.shared.config.settings import Settings, get_settings


@dataclass(frozen=True)
class CheckResult:
	"""One AWS/runtime readiness check result."""

	name: str
	passed: bool
	details: str


def run(
	*,
	settings: Settings | None = None,
	perform_bedrock_invoke: bool = False,
	perform_ses_send: bool = False,
	ses_target_email: str | None = None,
) -> int:
	"""Run deterministic AWS/runtime readiness checks and print machine-readable results."""
	cfg = settings or get_settings()
	results: list[CheckResult] = []

	results.append(_check_database_ready())
	results.extend(_check_ses_runtime(cfg, perform_ses_send=perform_ses_send, ses_target_email=ses_target_email))
	results.extend(_check_bedrock_runtime(cfg, perform_bedrock_invoke=perform_bedrock_invoke))

	for result in results:
		print(f'verify_aws_runtime_{result.name}={result.passed}')
		if result.details:
			print(f'verify_aws_runtime_{result.name}_details={result.details}')

	return 0 if all(result.passed for result in results) else 1


def _check_database_ready() -> CheckResult:
	session_factory = get_session_factory()
	try:
		with session_factory() as session:
			session.execute(text('SELECT 1'))
	except Exception as exc:
		return CheckResult(
			name='database_ready',
			passed=False,
			details=f'error={type(exc).__name__}:{exc}',
		)

	return CheckResult(name='database_ready', passed=True, details='ok')


def _check_ses_runtime(
	settings: Settings,
	*,
	perform_ses_send: bool,
	ses_target_email: str | None,
) -> list[CheckResult]:
	if settings.email_delivery_backend != 'ses':
		return [
			CheckResult(
				name='ses_runtime_configured',
				passed=True,
				details=f"skipped email_delivery_backend={settings.email_delivery_backend}",
			)
		]

	try:
		ses_client = _build_boto3_client('sesv2', region_name=settings.aws_region)
		account = ses_client.get_account()
	except Exception as exc:
		return [
			CheckResult(
				name='ses_runtime_configured',
				passed=False,
				details=f'error={type(exc).__name__}:{exc}',
			)
		]

	results = [
		CheckResult(
			name='ses_runtime_configured',
			passed=True,
			details=f"production_access_enabled={bool((account or {}).get('ProductionAccessEnabled', False))}",
		)
	]

	if not perform_ses_send:
		results.append(
			CheckResult(
				name='ses_send_probe',
				passed=True,
				details='skipped perform_ses_send=false',
			)
		)
		return results

	if not ses_target_email:
		results.append(
			CheckResult(
				name='ses_send_probe',
				passed=False,
				details='ses_target_email is required when perform_ses_send=true',
			)
		)
		return results

	try:
		response = ses_client.send_email(
			FromEmailAddress=settings.email_sender,
			Destination={'ToAddresses': [ses_target_email]},
			Content={
				'Simple': {
					'Subject': {'Data': 'UTW AWS readiness probe', 'Charset': 'UTF-8'},
					'Body': {
						'Text': {
							'Data': 'This is a controlled AWS readiness probe from UAE Tender Watch.',
							'Charset': 'UTF-8',
						}
					},
				}
			},
		)
		message_id = str((response or {}).get('MessageId', '')).strip()
		results.append(
			CheckResult(
				name='ses_send_probe',
				passed=bool(message_id),
				details=f'message_id={message_id or "missing"}',
			)
		)
	except Exception as exc:
		results.append(
			CheckResult(
				name='ses_send_probe',
				passed=False,
				details=f'error={type(exc).__name__}:{exc}',
			)
		)

	return results


def _check_bedrock_runtime(
	settings: Settings,
	*,
	perform_bedrock_invoke: bool,
) -> list[CheckResult]:
	if settings.ai_provider != 'bedrock_anthropic':
		return [
			CheckResult(
				name='bedrock_runtime_configured',
				passed=True,
				details=f"skipped ai_provider={settings.ai_provider}",
			)
		]

	try:
		runtime = build_ai_runtime(settings)
		input_tokens = estimate_bedrock_converse_input_tokens(
			model_id=settings.ai_model,
			messages=[
				SystemMessage(content='You are a readiness probe.'),
				UserMessage(content='Return the word ready.'),
			],
			settings=settings,
		)
	except (AIRuntimeDependencyError, Exception) as exc:
		return [
			CheckResult(
				name='bedrock_runtime_configured',
				passed=False,
				details=f'error={type(exc).__name__}:{exc}',
			)
		]

	results = [
		CheckResult(
			name='bedrock_runtime_configured',
			passed=runtime.llm is not None,
			details=f'count_tokens_input={input_tokens}',
		)
	]

	if not perform_bedrock_invoke:
		results.append(
			CheckResult(
				name='bedrock_invoke_probe',
				passed=True,
				details='skipped perform_bedrock_invoke=false',
			)
		)
		return results

	if runtime.llm is None:
		results.append(
			CheckResult(
				name='bedrock_invoke_probe',
				passed=False,
				details='primary llm was not configured',
			)
		)
		return results

	try:
		response_text = asyncio.run(_invoke_bedrock_probe(runtime.llm))
		results.append(
			CheckResult(
				name='bedrock_invoke_probe',
				passed='ready' in response_text.lower(),
				details=f'response={response_text[:120]}',
			)
		)
	except Exception as exc:
		results.append(
			CheckResult(
				name='bedrock_invoke_probe',
				passed=False,
				details=f'error={type(exc).__name__}:{exc}',
			)
		)

	return results


async def _invoke_bedrock_probe(llm: Any) -> str:
	completion = await llm.ainvoke(
		[
			SystemMessage(content='Respond using a single lowercase word.'),
			UserMessage(content='ready'),
		]
	)
	if hasattr(completion, 'completion'):
		return str(completion.completion)
	return str(completion)


def _build_boto3_client(service_name: str, *, region_name: str):
	try:
		import boto3
	except ImportError as exc:
		raise RuntimeError(
			'AWS readiness verification requires boto3. Install AWS dependencies with `uv sync --extra aws`.'
		) from exc

	return boto3.client(service_name, region_name=region_name)


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description='Verify AWS runtime readiness for production deployment.')
	parser.add_argument(
		'--perform-bedrock-invoke',
		action='store_true',
		help='Perform a live Bedrock model invoke after CountTokens succeeds.',
	)
	parser.add_argument(
		'--perform-ses-send',
		action='store_true',
		help='Perform a live SES send probe to the provided target address.',
	)
	parser.add_argument(
		'--ses-target-email',
		default=None,
		help='Target recipient for the optional SES send probe.',
	)
	return parser.parse_args()


if __name__ == '__main__':
	args = _parse_args()
	raise SystemExit(
		run(
			perform_bedrock_invoke=args.perform_bedrock_invoke,
			perform_ses_send=args.perform_ses_send,
			ses_target_email=args.ses_target_email,
		)
	)
