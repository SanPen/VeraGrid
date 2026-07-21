# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path

import chardet


def can_decode(data: bytes, encoding: str) -> bool:
    """
    Check whether a byte sequence can be decoded with a specific encoding.

    :param data: Raw byte sequence to validate.
    :param encoding: Candidate text encoding.
    :return: ``True`` when decoding succeeds, ``False`` otherwise.
    """
    can_decode_flag: bool = False

    # Try the decoding step because the detector output is only a heuristic.
    try:
        data.decode(encoding)
        can_decode_flag = True
    except LookupError:
        # Invalid encoding names must be rejected because they cannot decode data.
        can_decode_flag = False
    except UnicodeDecodeError:
        # Invalid byte sequences must be rejected because the file is not compatible with the encoding.
        can_decode_flag = False
    else:
        can_decode_flag = True

    return can_decode_flag


def detect_character_encoding(
    source: str | Path | bytes,
    fallback_encodings: tuple[str, ...] | None = None,
) -> str:
    """
    Detect a text encoding and validate the result by decoding the payload.

    The algorithm starts with ``chardet`` because it is cheap and already
    available in the project. The algorithm then validates the detected
    encoding by actually decoding the full byte sequence. If the detected
    encoding fails, the algorithm tries a short sequence of explicit fallback
    encodings that commonly appear in imported text files.

    :param source: File path or raw bytes to inspect.
    :param fallback_encodings: Optional ordered list of fallback encodings.
    :return: The first encoding that decodes the full payload.
    """
    data: bytes
    detection: dict[str, str | float | None]
    detected_encoding: str | None
    encodings_to_try: list[str] = list()
    encoding: str
    detected_text: str

    # Load the byte payload first because the detector and the validator both
    # need access to the same exact data.
    if isinstance(source, bytes):
        data = source
    else:
        data = Path(source).read_bytes()

    # Ask chardet for a first guess because it is a useful heuristic when the
    # file contains enough non-ASCII information.
    detection = chardet.detect(data)

    # Extract the detected encoding only when it is a proper string because
    # chardet may legitimately return ``None``.
    detected_encoding = None
    if isinstance(detection.get("encoding", None), str):
        detected_text = detection.get("encoding", None)
        if detected_text != "":
            detected_encoding = detected_text
        else:
            detected_encoding = None
    else:
        detected_encoding = None

    # Start with the detector output because the heuristic is often correct and
    # gives the shortest successful path.
    if detected_encoding is not None:
        encodings_to_try.append(detected_encoding)
    else:
        pass

    # Add explicit fallbacks because text imports often come from Windows tools
    # and may contain bytes that break a naive UTF-8 assumption.
    if fallback_encodings is None:
        encodings_to_try.append("utf-8")
        encodings_to_try.append("utf-8-sig")
        encodings_to_try.append("cp1252")
        encodings_to_try.append("latin-1")
    else:
        for encoding in fallback_encodings:
            if encoding not in encodings_to_try:
                encodings_to_try.append(encoding)
            else:
                pass

    # Validate each candidate by full decode because only a real decode can
    # prove that the candidate is compatible with the payload.
    for encoding in encodings_to_try:
        if can_decode(data=data, encoding=encoding):
            return encoding
        else:
            pass

    # Return a safe default instead of throwing because callers may still want
    # to decide how to handle undecodable files.
    return ""
