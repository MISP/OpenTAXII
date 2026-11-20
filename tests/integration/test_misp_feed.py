import json
import os
import ssl
import subprocess
from pathlib import Path
from shutil import which
from threading import Thread
from urllib.parse import urljoin
from uuid import uuid4

import pytest
from werkzeug.serving import make_server

from opentaxii.taxii2.entities import ApiRoot, Collection

FIXTURES = Path(__file__).with_name("fixtures")
API_ROOT = ApiRoot(
    uuid4(), default=True, title="CIRCL OSINT", description=None, is_public=True
)
COLLECTION = Collection(
    uuid4(),
    API_ROOT.id,
    "MISP feed",
    "",
    alias=None,
    is_public=True,
    is_public_write=True,
)
pytestmark = [
    pytest.mark.truncate,
    pytest.mark.skipif(
        not os.environ.get("TAXII21_CLIENT_ENV"),
        reason="run with tox -e py312-feed-round-trip",
    ),
]


@pytest.fixture
def cabby_cli():
    client_env = Path(os.environ["TAXII21_CLIENT_ENV"])
    scripts = client_env / ("Scripts" if os.name == "nt" else "bin")
    executable = which("taxii-21", path=str(scripts))
    assert executable, f"Cabby CLI missing from {scripts}"
    return executable


@pytest.fixture
def taxii_https(app, tmp_path):
    import trustme

    # The unit-test fixture uses a 1 KiB limit. The feed produces larger bundles.
    app.taxii_server.servers.taxii2.config["max_content_length"] = 64 * 1024
    ca = trustme.CA()
    cert_path = tmp_path / "ca.pem"
    ca.cert_pem.write_to_path(cert_path)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ca.issue_cert("127.0.0.1").configure_cert(tls)

    with make_server("127.0.0.1", 0, app, ssl_context=tls) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"https://127.0.0.1:{server.server_port}/", cert_path
        finally:
            server.shutdown()
            thread.join()


def run_cabby(executable, url, ca_cert, *args):
    result = subprocess.run(
        [executable, url, "--ca-cert", str(ca_cert), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        env={**os.environ, "NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"},
    )
    assert result.returncode == 0, result.stderr
    return [json.loads(line) for line in result.stdout.splitlines()]


@pytest.mark.parametrize("db_api_roots", [(API_ROOT,)], indirect=True)
@pytest.mark.parametrize("db_collections", [(COLLECTION,)], indirect=True)
@pytest.mark.parametrize(
    "event_uuid",
    ("568ee522-23ac-4002-b82d-4d1402de0b81", "56f419c3-e67c-45fc-b3a6-40d5950d210f"),
)
def test_misp_feed_round_trip(
    event_uuid, tmp_path, db_collections, taxii_https, cabby_cli
):
    from misp_stix_converter import misp_to_stix2

    source = FIXTURES / f"{event_uuid}.json"
    bundle_path = tmp_path / f"{event_uuid}.stix.json"
    conversion = misp_to_stix2(source, version="2.1", output_name=bundle_path)
    assert conversion.get("success") == 1 and not conversion.get("errors"), conversion
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["type"] == "bundle"
    objects = bundle["objects"]
    event = json.loads(source.read_text(encoding="utf-8"))["Event"]
    indicator = next(
        attribute for attribute in event["Attribute"] if attribute["to_ids"]
    )
    assert any(
        obj["id"] == f"indicator--{indicator['uuid']}" and obj["spec_version"] == "2.1"
        for obj in objects
    )

    # Cabby uploads a TAXII envelope containing the bundle's objects.
    envelope = tmp_path / f"{event_uuid}.taxii.json"
    envelope.write_text(json.dumps({"objects": objects}), encoding="utf-8")
    origin, ca_cert = taxii_https
    (discovery,) = run_cabby(cabby_cli, urljoin(origin, "taxii2/"), ca_cert, "discover")
    api_root = urljoin(origin, discovery["default"])
    collection_id = str(db_collections[0].id)

    (submission,) = run_cabby(
        cabby_cli, api_root, ca_cert, "add", collection_id, str(envelope)
    )
    (job,) = run_cabby(cabby_cli, api_root, ca_cert, "status", submission["id"])
    assert job["status"] == "complete"
    assert job["total_count"] == job["success_count"] == len(objects)
    assert job["failure_count"] == job["pending_count"] == 0

    pages = run_cabby(
        cabby_cli, api_root, ca_cert, "objects", collection_id, "--limit", "3"
    )
    assert len(pages) > 1 and pages[0]["more"] is True and pages[-1]["more"] is False
    retrieved = [obj for page in pages for obj in page["objects"]]
    assert sorted(retrieved, key=lambda obj: obj["id"]) == sorted(
        objects, key=lambda obj: obj["id"]
    )
