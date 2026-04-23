from __future__ import annotations

from types import SimpleNamespace

from src.scripts.verify_aws_runtime_readiness import run


class _FakeSession:
	def execute(self, statement):
		return None

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc, tb):
		return False


def test_run_reports_success_for_configured_ses_and_bedrock(monkeypatch, capsys) -> None:
	settings = SimpleNamespace(
		email_delivery_backend='ses',
		aws_region='us-east-1',
		email_sender='alerts@example.com',
		ai_provider='bedrock_anthropic',
		ai_model='anthropic.test-model',
	)

	monkeypatch.setattr(
		'src.scripts.verify_aws_runtime_readiness.get_session_factory',
		lambda: lambda: _FakeSession(),
	)
	monkeypatch.setattr(
		'src.scripts.verify_aws_runtime_readiness._build_boto3_client',
		lambda service_name, *, region_name: (
			SimpleNamespace(get_account=lambda: {'ProductionAccessEnabled': True})
			if service_name == 'sesv2'
			else SimpleNamespace()
		),
	)
	monkeypatch.setattr(
		'src.scripts.verify_aws_runtime_readiness.build_ai_runtime',
		lambda settings: SimpleNamespace(llm=SimpleNamespace(), fallback_llm=None),
	)
	monkeypatch.setattr(
		'src.scripts.verify_aws_runtime_readiness.estimate_bedrock_converse_input_tokens',
		lambda *, model_id, messages, settings: 42,
	)

	exit_code = run(settings=settings)

	assert exit_code == 0
	output = capsys.readouterr().out
	assert 'verify_aws_runtime_database_ready=True' in output
	assert 'verify_aws_runtime_ses_runtime_configured=True' in output
	assert 'verify_aws_runtime_bedrock_runtime_configured=True' in output
	assert 'verify_aws_runtime_bedrock_invoke_probe=True' in output


def test_run_fails_closed_when_bedrock_count_tokens_fails(monkeypatch, capsys) -> None:
	settings = SimpleNamespace(
		email_delivery_backend='dev_outbox',
		aws_region='us-east-1',
		email_sender='alerts@example.com',
		ai_provider='bedrock_anthropic',
		ai_model='anthropic.test-model',
	)

	monkeypatch.setattr(
		'src.scripts.verify_aws_runtime_readiness.get_session_factory',
		lambda: lambda: _FakeSession(),
	)
	monkeypatch.setattr(
		'src.scripts.verify_aws_runtime_readiness.build_ai_runtime',
		lambda settings: SimpleNamespace(llm=SimpleNamespace(), fallback_llm=None),
	)
	monkeypatch.setattr(
		'src.scripts.verify_aws_runtime_readiness.estimate_bedrock_converse_input_tokens',
		lambda *, model_id, messages, settings: (_ for _ in ()).throw(RuntimeError('AccessDenied')),
	)

	exit_code = run(settings=settings)

	assert exit_code == 1
	output = capsys.readouterr().out
	assert 'verify_aws_runtime_bedrock_runtime_configured=False' in output
	assert 'AccessDenied' in output
