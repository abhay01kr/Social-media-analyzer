import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from config import UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_VIDEO_EXTENSIONS
from services.video_analyzer import video_metadata_analyzer
from services.duplicate_detector import duplicate_detector
from services.ai_detector import ai_media_detector
from database.db import save_report

router = APIRouter(prefix="/api/videos", tags=["Videos"])

def remove_temp_file(file_path: Path):
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Error removing temporary file {file_path}: {e}")

@router.post("/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    keep_file: Optional[bool] = Form(False)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No video file provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format: '{ext}'. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Generate unique safe filename
    unique_id = str(uuid.uuid4())
    safe_filename = f"{unique_id}_{Path(file.filename).name}"
    save_path = UPLOAD_DIR / safe_filename

    try:
        # Stream file to disk while validating max file size
        total_bytes = 0
        with open(save_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
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

        # 3. AI media / deepfake estimation
        ai_result = ai_media_detector.analyze(sampled_frames, meta_result)

        # 4. Construct overall consolidated response
        authenticity_score = ai_result.get("authenticity_score", 85.0)
        overall_verdict = ai_result.get("risk_badge", "Authentic")
        summary_text = (
            f"Read {meta_result.get('frame_count')} frames at {meta_result.get('fps')} FPS "
            f"({meta_result.get('duration')}s). {ai_result.get('summary')}"
        )

        full_data = {
            "report_id": unique_id,
            "filename": file.filename,
            "metadata": meta_result,
            "ai_analysis": ai_result,
            "duplicate_analysis": duplicate_result,
            "authenticity_score": authenticity_score,
            "deepfake_probability": ai_result.get("ai_likelihood_score", 15.0),
            "verdict": overall_verdict,
            "summary": summary_text
        }

        # 5. Persist to database
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

        # Remove temporary file if keep_file is False to protect user privacy and disk space
        if not keep_file:
            background_tasks.add_task(remove_temp_file, save_path)

        return full_data

    except HTTPException:
        raise
    except Exception as e:
        if not keep_file and save_path.exists():
            save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")

@router.post("/reference")
async def add_reference_video(
    title: str = Form(...),
    file: UploadFile = File(...)
):
    """Allows registering a known video into reference collection for duplicate detection."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid format {ext}")

    ref_id = str(uuid.uuid4())
    temp_path = UPLOAD_DIR / f"ref_{ref_id}_{file.filename}"

    with open(temp_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    try:
        meta = video_metadata_analyzer.analyze_file(temp_path)
        sampled = meta.pop("sampled_frames_data", [])
        fingerprints = duplicate_detector.generate_fingerprint(sampled)
        duplicate_detector.add_reference(ref_id, title, fingerprints, {
            "filename": file.filename,
            "duration": meta.get("duration"),
            "fps": meta.get("fps")
        })
        return {
            "status": "success",
            "message": f"Video registered as reference: '{title}'",
            "reference_id": ref_id,
            "fingerprints_count": len(fingerprints)
        }
    finally:
        if temp_path.exists():
            temp_path.unlink()
