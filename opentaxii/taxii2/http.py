"""Taxii2 http helper functions."""

import json
import uuid
from typing import Dict, Optional

from flask import Response, make_response
from werkzeug.datastructures import MIMEAccept
from werkzeug.http import parse_options_header

TAXII_MEDIA_TYPE = "application/taxii+json"


def _parse_media_type(value: Optional[str]) -> tuple[str, dict[str, str]]:
    media_type, parameters = parse_options_header(value)
    return media_type.lower(), {
        name.lower(): value for name, value in parameters.items()
    }


def accepts_media_type(accept: MIMEAccept, supported: str) -> bool:
    """Check the quality of the most specific range matching a representation."""
    media_type, parameters = _parse_media_type(supported)
    main_type = media_type.split("/", 1)[0]
    matching_types = {media_type, f"{main_type}/*", "*/*"}
    # Werkzeug orders the ranges by specificity, then descending quality.
    for media_range, quality in accept:
        accepted_type, accepted_parameters = _parse_media_type(media_range)
        if (
            accepted_type in matching_types
            and accepted_parameters.items() <= parameters.items()
        ):
            return quality > 0
    return False


def matches_content_type(content_type: Optional[str], supported: str) -> bool:
    """Compare parsed request media types and allow the implicit TAXII version."""
    media_type, parameters = _parse_media_type(supported)
    if (
        media_type == TAXII_MEDIA_TYPE
        and parameters.keys() <= {"version"}
        and content_type is not None
        and content_type.strip().lower() == TAXII_MEDIA_TYPE
    ):
        return True
    return _parse_media_type(content_type) == (media_type, parameters)


class UuidJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def make_taxii2_response(
    data, status: Optional[int] = 200, extra_headers: Optional[Dict] = None
) -> Response:
    """Turn input data into valid taxii2 response."""
    if not isinstance(data, str):
        data = json.dumps(data, cls=UuidJsonEncoder)
    response = make_response((data, status))
    response.content_type = "application/taxii+json;version=2.1"
    response.headers.update(extra_headers or {})
    return response
