from app.models.payloads import AgentRun


def test_agent_run_defaults():
    run = AgentRun(request_id="abc", input="hello")
    assert run.status == "pending"
    assert run.metadata == {}
    assert run.response is None or isinstance(run.response, dict)
