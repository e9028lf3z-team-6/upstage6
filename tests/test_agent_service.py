def test_agent_decision(agent_service):
    response = agent_service.process_query(
        "지금 런던 지사에 회의 요청해도 돼?"
    )

    assert "ai_message" in response
    assert response["ai_message"] is not None
