import json
from uuid import uuid4

import pytest

TAXII_21 = "application/taxii+json;version=2.1"


@pytest.mark.parametrize(
    "accept, status",
    [
        pytest.param("application/taxii+json", 200, id="versionless"),
        pytest.param(TAXII_21, 200, id="explicit-version"),
        pytest.param(
            'Application/TAXII+JSON; Version="2.1"', 200, id="equivalent-parameters"
        ),
        pytest.param("application/*", 200, id="wildcard"),
        pytest.param(
            "application/taxii+json;version=2.0", 406, id="unsupported-version"
        ),
        pytest.param(
            "application/taxii+json;version=2.0, application/taxii+json;q=0.5",
            200,
            id="supported-fallback",
        ),
        pytest.param(f"{TAXII_21};q=0", 406, id="zero-quality"),
        pytest.param(
            f"{TAXII_21};q=0, application/taxii+json;q=1, */*;q=1",
            406,
            id="specific-rejection-overrides-fallbacks",
        ),
        pytest.param(None, 406, id="missing"),
    ],
)
def test_accept_negotiation(client, accept, status):
    headers = {"Accept": accept} if accept is not None else {}
    response = client.get("/taxii2/", headers=headers)
    assert response.status_code == status
    assert response.content_type == TAXII_21


@pytest.mark.parametrize(
    "content_type, status",
    [
        pytest.param(TAXII_21, 202, id="explicit-version"),
        pytest.param("application/taxii+json; version=2.1", 202, id="whitespace"),
        pytest.param(
            'Application/TAXII+JSON; Version="2.1"', 202, id="equivalent-parameters"
        ),
        pytest.param("application/taxii+json", 202, id="versionless"),
        pytest.param(
            "application/taxii+json;version=2.0", 415, id="unsupported-version"
        ),
        pytest.param("application/json", 415, id="unsupported-type"),
    ],
)
def test_add_objects_content_type(client, db_collections, content_type, status):
    collection = db_collections[-1]
    url = f"/taxii2/{collection.api_root_id}/collections/{collection.id}/objects/"
    obj = {
        "id": f"identity--{uuid4()}",
        "type": "identity",
        "spec_version": "2.1",
        "created": "2024-01-01T00:00:00.000Z",
        "modified": "2024-01-01T00:00:00.000Z",
        "name": "Negotiation test",
        "identity_class": "organization",
    }
    response = client.post(
        url,
        headers={"Accept": TAXII_21},
        content_type=content_type,
        data=json.dumps({"objects": [obj]}),
    )
    assert response.status_code == status
    assert response.content_type == TAXII_21
    if status == 202:
        assert response.get_json()["success_count"] == 1
