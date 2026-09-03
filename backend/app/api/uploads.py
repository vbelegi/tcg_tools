"""Shared upload helpers."""

from __future__ import annotations

from fastapi import HTTPException, UploadFile


async def read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    """Read an upload in chunks, refusing anything over max_bytes."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail="Arquivo muito grande.")
        chunks.append(chunk)
    return b"".join(chunks)
