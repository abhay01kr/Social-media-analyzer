import cv2
import os
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

class VideoMetadataAnalyzer:
    """
    Extracts video metadata and verifies decode integrity using OpenCV.
    Follows project guidelines:
    - Distinguishes file integrity from analysis coverage.
    - Accurately measures duration, FPS, frame count, and file readability.
    """

    def __init__(self, max_sample_frames: int = 50):
        self.max_sample_frames = max_sample_frames

    def analyze_file(self, file_path: str | Path) -> Dict[str, Any]:
        path = str(file_path)
        if not os.path.exists(path):
            return {
                "readable": False,
                "error": f"File not found: {path}",
                "duration": 0.0,
                "fps": 0.0,
                "frame_count": 0,
                "resolution": "0x0",
                "integrity": {
                    "decodable": False,
                    "header_valid": False,
                    "notes": "File does not exist on disk."
                },
                "coverage": {
                    "sampled_frames": 0,
                    "coverage_percent": 0.0,
                    "notes": "No frames could be inspected."
                }
            }

        file_size_bytes = os.path.getsize(path)
        cap = cv2.VideoCapture(path)

        if not cap.isOpened():
            cap.release()
            return {
                "readable": False,
                "error": "Failed to open video container with OpenCV decoder.",
                "duration": 0.0,
                "fps": 0.0,
                "frame_count": 0,
                "resolution": "0x0",
                "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
                "integrity": {
                    "decodable": False,
                    "header_valid": False,
                    "notes": "Container could not be parsed or unsupported video codec."
                },
                "coverage": {
                    "sampled_frames": 0,
                    "coverage_percent": 0.0,
                    "notes": "Zero frames sampled."
                }
            }

        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        reported_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)
        fourcc_str = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]) if fourcc_int != 0 else "Unknown"

        # Read first frame to verify decodability
        ret, first_frame = cap.read()
        can_decode_first_frame = bool(ret and first_frame is not None and first_frame.size > 0)

        # Calculate duration
        duration = 0.0
        if fps > 0 and reported_frame_count > 0:
            duration = round(reported_frame_count / fps, 2)

        # Sample frames across the video timeline to test stream integrity and coverage
        sampled_frames = []
        actual_sampled_count = 0
        decode_failures = 0

        if can_decode_first_frame and reported_frame_count > 0:
            step = max(1, reported_frame_count // self.max_sample_frames)
            for frame_idx in range(0, reported_frame_count, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                s_ret, s_frame = cap.read()
                if s_ret and s_frame is not None:
                    actual_sampled_count += 1
                    # Keep a small downscaled version in memory for subsequent analyzers
                    small_frame = cv2.resize(s_frame, (160, 160))
                    sampled_frames.append((frame_idx, small_frame))
                else:
                    decode_failures += 1
                if len(sampled_frames) >= self.max_sample_frames:
                    break

        cap.release()

        # Compute aspect ratio string
        aspect_ratio_str = "Unknown"
        if width > 0 and height > 0:
            gcd = math.gcd(width, height)
            rw, rh = width // gcd, height // gcd
            if (rw, rh) in [(16, 9), (9, 16), (4, 3), (1, 1), (21, 9)]:
                aspect_ratio_str = f"{rw}:{rh}"
            else:
                aspect_ratio_str = f"{round(width/height, 2)}:1"

        coverage_percent = round((actual_sampled_count / max(1, reported_frame_count)) * 100, 2) if reported_frame_count > 0 else 0.0
        is_complete_stream = (decode_failures == 0 and can_decode_first_frame)

        return {
            "readable": can_decode_first_frame,
            "duration": duration,
            "fps": round(fps, 2),
            "frame_count": reported_frame_count,
            "resolution": f"{width}x{height}",
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio_str,
            "codec": fourcc_str.strip(),
            "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
            "integrity": {
                "header_valid": True,
                "decodable": can_decode_first_frame,
                "complete_stream": is_complete_stream,
                "decode_failures": decode_failures,
                "notes": "Verified frame decoding and container header integrity via OpenCV."
            },
            "coverage": {
                "sampled_frames": actual_sampled_count,
                "coverage_percent": coverage_percent,
                "notes": f"Sampled {actual_sampled_count} frames evenly across video timeline."
            },
            "sampled_frames_data": sampled_frames
        }

video_metadata_analyzer = VideoMetadataAnalyzer()
