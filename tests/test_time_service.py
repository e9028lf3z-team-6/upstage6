def test_time_service_returns_time(time_service):
    result = time_service.get_current_time("Europe/London")
    assert result.hhmm is not None
    assert ":" in result.hhmm
