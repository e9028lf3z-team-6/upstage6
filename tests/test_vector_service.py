def test_vector_insert_and_search(vector_service):
    docs = ["런던 지사 점심시간은 12:00~13:00 입니다."]
    vector_service.add_documents(docs)

    results = vector_service.search_for_agent("런던 점심시간")
    assert len(results) > 0
    assert "점심시간" in results[0]
