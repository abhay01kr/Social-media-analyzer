import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from config import UPLOAD_DIR

class CloudinaryService:
    """
    Cloudinary Media Storage Service for Member 6.
    Uploads images, videos, and generated PDF reports to Cloudinary CDN.
    If Cloudinary credentials are not configured, gracefully falls back to local storage.
    """

    def __init__(self):
        self.cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        self.api_key = os.getenv("CLOUDINARY_API_KEY")
        self.api_secret = os.getenv("CLOUDINARY_API_SECRET")
        self._is_configured = bool(self.cloud_name and self.api_key and self.api_secret)
        
        if self._is_configured:
            try:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(
                    cloud_name=self.cloud_name,
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    secure=True
                )
                print(f"[Cloudinary] Configured successfully for cloud: {self.cloud_name}")
            except ImportError:
                self._is_configured = False
                print("[Cloudinary] Cloudinary package not installed. Using local storage fallback.")

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    def upload_file(self, file_path: Path, resource_type: str = "auto", folder: str = "social_media_analyzer") -> Dict[str, Any]:
        """
        Uploads local file to Cloudinary or falls back to local static URL.
        """
        if self._is_configured:
            try:
                import cloudinary.uploader
                result = cloudinary.uploader.upload(
                    str(file_path),
                    resource_type=resource_type,
                    folder=folder
                )
                return {
                    "provider": "cloudinary",
                    "public_id": result.get("public_id"),
                    "url": result.get("secure_url", result.get("url")),
                    "format": result.get("format"),
                    "bytes": result.get("bytes")
                }
            except Exception as e:
                print(f"[Cloudinary] Upload failed ({e}), returning local path.")

        # Local storage fallback
        dest_filename = file_path.name
        dest_path = UPLOAD_DIR / dest_filename
        if file_path.resolve() != dest_path.resolve():
            shutil.copyfile(file_path, dest_path)

        return {
            "provider": "local",
            "public_id": dest_filename,
            "url": f"/uploads/{dest_filename}",
            "format": file_path.suffix.lstrip("."),
            "bytes": file_path.stat().st_size if file_path.exists() else 0
        }

cloudinary_service = CloudinaryService()
