import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status
from config import UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_VIDEO_EXTENSIONS
from services.image_analyzer import image_analyzer
from services.video_analyzer import video_metadata_analyzer
from services.duplicate_detector import duplicate_detector
from services.ai_detector import ai_media_detector
from services.cloudinary_service import cloudinary_service
from database.db_unified import save_report

router = APIRouter(tags=["Member 3 - Image & Video Analyzer"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def remove_temp_file(file_path: Path):
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Error removing temporary file {file_path}: {e}")

# ==================== IMAGE ANALYZER (/analyze/image) ====================

@router.post("/analyze/image")
@router.post("/api/analyze/image")
async def analyze_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    keep_file: Optional[bool] = Form(False)
):
    """
    Member 3 - Image Analyzer Endpoint.
    Analyzes:
    - AI-generated Image Detection
    - Deepfake Detection
    - Face Detection
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No image file provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format: '{ext}'. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    unique_id = str(uuid.uuid4())
    safe_filename = f"img_{unique_id}_{Path(file.filename).name}"
    save_path = UPLOAD_DIR / safe_filename

    try:
        total_bytes = 0
        with open(save_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > 50 * 1024 * 1024:  # 50MB image limit
                    buffer.close()
                    save_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="Image exceeds 50MB limit.")
                buffer.write(chunk)
    except Exception as e:
        if save_path.exists():
            save_path.unlink(missing_ok=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to save image upload: {str(e)}")

    try:
        # Run Member 3 image forensic pipeline
        analysis_result = image_analyzer.analyze_file(save_path)
        analysis_result["report_id"] = unique_id

        # Upload to Cloudinary if configured (Member 6)
        cloud_meta = cloudinary_service.upload_file(save_path, resource_type="image")
        analysis_result["media_url"] = cloud_meta.get("url")
        analysis_result["storage_provider"] = cloud_meta.get("provider")

        # Persist report to MongoDB / Unified DB
        save_report(
            report_id=unique_id,
            report_type="image",
            target=file.filename,
            status="completed",
            score=analysis_result["authenticity_score"],
            verdict=analysis_result["risk_badge"],
            summary=analysis_result["summary"],
            data=analysis_result
        )

        if not keep_file:
            background_tasks.add_task(remove_temp_file, save_path)

        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        if not keep_file and save_path.exists():
            save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

# ==================== VIDEO ANALYZER (/analyze/video) ====================

@router.post("/analyze/video")
@router.post("/api/analyze/video")
@router.post("/api/videos/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    keep_file: Optional[bool] = Form(False)
):
    """
    Member 3 - Video Analyzer Endpoint.
    Analyzes:
    - AI-generated Video Detection
    - Deepfake Detection
    - Video Metadata Analysis
    - Face Detection
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No video file provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format: '{ext}'. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    unique_id = str(uuid.uuid4())
    safe_filename = f"vid_{unique_id}_{Path(file.filename).name}"
    save_path = UPLOAD_DIR / safe_filename

    try:
        total_bytes = 0
        with open(save_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_SIZE:
                    buffer.close()
                    save_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024*1024)}MB."
                    )
                buffer.write(chunk)
    except Exception as e:
        if save_path.exists():
            save_path.unlink(missing_ok=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to save video upload: {str(e)}")

    try:
        # 1. Video metadata extraction and stream decode check (OpenCV)
        meta_result = video_metadata_analyzer.analyze_file(save_path)
        sampled_frames = meta_result.pop("sampled_frames_data", [])

        if not meta_result.get("readable"):
            raise HTTPException(
                status_code=422,
                detail=f"Video file cannot be decoded by OpenCV. {meta_result.get('error', '')}"
            )

        # 2. Duplicate detection against reference database
        duplicate_result = duplicate_detector.check_duplicate(sampled_frames)

        # 3. AI media, Face Detection, and Deepfake estimation
        ai_result = ai_media_detector.analyze(sampled_frames, meta_result)

        # 4. Upload to Cloudinary if configured (Member 6)
        cloud_meta = cloudinary_service.upload_file(save_path, resource_type="video")

        authenticity_score = ai_result.get("authenticity_score", 85.0)
        overall_verdict = ai_result.get("risk_badge", "Authentic")
        summary_text = (
            f"Read {meta_result.get('frame_count')} frames at {meta_result.get('fps')} FPS "
            f"({meta_result.get('duration')}s). {ai_result.get('summary')}"
        )

        full_data = {
            "report_id": unique_id,
            "filename": file.filename,
            "media_type": "video",
            "media_url": cloud_meta.get("url"),
            "storage_provider": cloud_meta.get("provider"),
            "metadata": meta_result,
            "face_detection": ai_result.get("face_detection", {}),
            "ai_analysis": ai_result,
            "deepfake_analysis": ai_result.get("deepfake_analysis", {}),
            "duplicate_analysis": duplicate_result,
            "authenticity_score": authenticity_score,
            "deepfake_probability": ai_result.get("deepfake_probability", 10.0),
            "ai_likelihood_score": ai_result.get("ai_likelihood_score", 15.0),
            "verdict": overall_verdict,
            "summary": summary_text
        }

        # 5. Persist to database (MongoDB / Unified DB)
        save_report(
            report_id=unique_id,
            report_type="video",
            target=file.filename,
            status="completed",
            score=authenticity_score,
            verdict=overall_verdict,
            summary=summary_text,
            data=full_data
        )

        if not keep_file:
            background_tasks.add_task(remove_temp_file, save_path)

        return full_data

    except HTTPException:
        raise
    except Exception as e:
        if not keep_file and save_path.exists():
            save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")
