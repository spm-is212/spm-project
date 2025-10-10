import os
from pathlib import Path
from typing import Optional
from uuid import uuid4
from urllib.parse import urlparse

from backend.wrappers.supabase_wrapper.supabase_client import SupabaseClient


class SupabaseStorage:

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

    def delete_file(self, file_url: str) -> bool:
        if not file_url:
            return False

        try:
            storage_path = self._extract_storage_path_from_url(file_url)
            if not storage_path:
                return False

            storage_bucket = self._client.storage.from_(self.bucket_name)
            response = storage_bucket.remove([storage_path])

            error = getattr(response, "error", None)
            if error:
                return False

            return True
        except Exception:
            return False

    def _extract_storage_path_from_url(self, file_url: str) -> Optional[str]:
        try:
            parsed_url = urlparse(file_url)
            path_parts = parsed_url.path.split(f"/object/public/{self.bucket_name}/")
            if len(path_parts) > 1:
                return path_parts[1]
            return None
        except Exception:
            return None
