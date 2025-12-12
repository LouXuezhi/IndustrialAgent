from app.core.response import StandardResponse


def test_standard_response_defaults():
    data = {"ok": True}
    resp = StandardResponse(data=data)
    assert resp.code == 0
    assert resp.message == "success"
    assert resp.data == data
    assert resp.timestamp is not None



