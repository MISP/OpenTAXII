import datetime

import pytest

from opentaxii.taxii2.utils import taxii2_datetimeformat
from tests.taxii2 import utils
from tests.taxii2.factories import STIXObjectFactory

COLLECTION = utils.COLLECTIONS[6]
DATE_ADDED = datetime.datetime(2024, 1, 3, tzinfo=datetime.timezone.utc)
OBJECT_ID = "identity--00000000-0000-4000-8000-000000000001"
SECOND_OBJECT_ID = "identity--00000000-0000-4000-8000-000000000002"
VERSIONS = [DATE_ADDED - datetime.timedelta(days=days) for days in (2, 1)]

TIED_OBJECTS = [
    STIXObjectFactory(
        id=object_id,
        collection_id=COLLECTION.id,
        type="identity",
        spec_version="2.1",
        date_added=DATE_ADDED,
        version=version,
        serialized_data={"modified": taxii2_datetimeformat(version)},
    )
    for object_id, version in (
        (OBJECT_ID, VERSIONS[1]),
        (OBJECT_ID, VERSIONS[0]),
        (SECOND_OBJECT_ID, VERSIONS[0]),
    )
]

ENDPOINTS = [
    pytest.param("objects/", "modified", 3, id="collection-objects"),
    pytest.param(f"objects/{OBJECT_ID}/", "modified", 2, id="object"),
    pytest.param("manifest/", "version", 3, id="manifest"),
    pytest.param(f"objects/{OBJECT_ID}/versions/", None, 2, id="versions"),
]


@pytest.fixture(params=["sql", "mock"])
def pagination_objects(request, db_stix_objects, taxii2_sqldb_api, monkeypatch):
    if request.param == "mock":
        monkeypatch.setattr(utils, "STIX_OBJECTS", tuple(db_stix_objects))
        monkeypatch.setattr(taxii2_sqldb_api, "get_object", utils.GET_OBJECT_MOCK)
        monkeypatch.setattr(taxii2_sqldb_api, "get_objects", utils.GET_OBJECTS_MOCK)
        monkeypatch.setattr(taxii2_sqldb_api, "get_manifest", utils.GET_MANIFEST_MOCK)
        monkeypatch.setattr(taxii2_sqldb_api, "get_versions", utils.GET_VERSIONS_MOCK)
    return db_stix_objects


@pytest.mark.parametrize("db_stix_objects", [TIED_OBJECTS], indirect=True)
@pytest.mark.parametrize("endpoint, version_field, record_count", ENDPOINTS)
def test_pagination_with_tied_dates(
    authenticated_client, pagination_objects, endpoint, version_field, record_count
):
    url = f"/taxii2/{COLLECTION.api_root_id}/collections/{COLLECTION.id}/{endpoint}"
    headers = {"Accept": "application/taxii+json;version=2.1"}
    filters: dict[str, int | str] = {"limit": 1}
    if version_field is not None:
        filters["match[version]"] = "all"
    expected = sorted(pagination_objects, key=lambda obj: (obj.id, obj.version))[
        :record_count
    ]

    for index, obj in enumerate(expected):
        response = authenticated_client.get(url, headers=headers, query_string=filters)
        assert response.status_code == 200
        assert response.headers["X-TAXII-Date-Added-Last"] == taxii2_datetimeformat(
            DATE_ADDED
        )
        body = response.get_json()
        expected_version = taxii2_datetimeformat(obj.version)
        if version_field is None:
            assert body["versions"] == [expected_version]
        else:
            (record,) = body["objects"]
            assert record["id"] == obj.id
            assert record[version_field] == expected_version

        more = index < record_count - 1
        assert body["more"] is more
        if more:
            filters["next"] = body["next"]
        else:
            assert "next" not in body


@pytest.mark.parametrize("endpoint, version_field, record_count", ENDPOINTS)
def test_pagination_rejects_zero_limit(
    authenticated_client, endpoint, version_field, record_count
):
    url = f"/taxii2/{COLLECTION.api_root_id}/collections/{COLLECTION.id}/{endpoint}"
    response = authenticated_client.get(
        url,
        headers={"Accept": "application/taxii+json;version=2.1"},
        query_string={"limit": 0},
    )
    assert response.status_code == 400
