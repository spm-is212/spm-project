import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from backend.wrappers.supabase_wrapper.supabase_client import SupabaseClient


class SupabaseStorage:
    """Wrapper around Supabase storage operations used by task endpoints."""

    def __init__(self, bucket_name: Optional[str] = None) -> None:
        self._client = SupabaseClient().client
        self.bucket_name = bucket_name or os.getenv("SUPABASE_TASK_FILES_BUCKET")
        if not self.bucket_name:
            raise ValueError("Supabase storage bucket name is not configured. Set SUPABASE_TASK_FILES_BUCKET.")

    def upload_file(
        self,
        *,
        file_name: str,
        file_bytes: bytes,
        content_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Upload a file to Supabase storage and return its public URL."""
        if not file_bytes:
            raise ValueError("Cannot upload an empty file.")

        safe_name = Path(file_name).name
        unique_name = f"{uuid4().hex}_{safe_name}"
        storage_path = f"tasks/{user_id}/{unique_name}" if user_id else f"tasks/{unique_name}"

        storage_bucket = self._client.storage.from_(self.bucket_name)
        options = {"content-type": content_type or "application/octet-stream", "upsert": False}
        response = storage_bucket.upload(storage_path, file_bytes, options)

        error = getattr(response, "error", None)
        if error:
            message = getattr(error, "message", None) or str(error)
            raise ValueError(f"Supabase storage upload failed: {message}")

        public_response = storage_bucket.get_public_url(storage_path)

        if isinstance(public_response, dict):
            data = public_response.get("data") or {}
            url = data.get("publicUrl") or data.get("public_url") or public_response.get("publicUrl") or public_response.get("public_url")
        else:
            data = getattr(public_response, "data", None)
            if isinstance(data, dict):
                url = data.get("publicUrl") or data.get("public_url")
            else:
                url = public_response

        if not url:
            raise ValueError("Supabase did not return a public URL for the uploaded file.")

        return url
