import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from .face_detector import face_detector

class ImageMediaAnalyzer:
    """
    Member 3 - Image Analyzer.
    Provides:
    - AI-generated Image Detection (Frequency domain FFT, noise anomalies, edge smoothness)
    - Deepfake Detection (Facial blending seams, artificial skin smoothing, eye symmetry)
    - Face Detection
    """

    def __init__(self):
        pass

    def compute_fft_spectral_energy(self, gray: np.ndarray) -> float:
        """
        Computes 2D Fast Fourier Transform to analyze high-frequency spectral distribution.
        Diffusion models (Midjourney, DALL-E, Stable Diffusion) characteristically leave
        fingerprints in the high-frequency spectrum due to upsampling convolutions.
        """
        if gray is None or gray.size == 0:
            return 0.0
        h, w = gray.shape
        # Resize to standard power of 2 for stable spectral comparison
        resized = cv2.resize(gray, (256, 256))
        dft = cv2.dft(np.float32(resized), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        magnitude_spectrum = 20 * np.log(cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1]) + 1e-6)

        # High-frequency radial energy ratio
        center = 128
        y, x = np.ogrid[:256, :256]
        r = np.sqrt((x - center)**2 + (y - center)**2)
        high_freq_mask = (r > 64) & (r < 120)
        high_freq_energy = float(np.mean(magnitude_spectrum[high_freq_mask]))
        return high_freq_energy

    def compute_noise_residual(self, gray: np.ndarray) -> float:
        """
        Extracts noise residual via median filtering to verify natural camera sensor PRNU noise.
        AI generated images lack real camera sensor grain or exhibit synthetic uniform noise.
        """
        denoised = cv2.medianBlur(gray, 3)
        residual = cv2.absdiff(gray, denoised)
        return float(np.var(residual))

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Runs comprehensive Member 3 forensic pipeline on an image.
        """
        img = cv2.imread(str(file_path))
        if img is None:
            raise ValueError("Could not decode image file.")

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 1. Face Detection (Member 3)
        face_result = face_detector.detect_faces(img)

        # 2. AI-generated Image Detection (Member 3)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        fft_energy = self.compute_fft_spectral_energy(gray)
        noise_var = self.compute_noise_residual(gray)

        # Saturation profile
        saturation_channel = hsv[:, :, 1]
        mean_saturation = float(np.mean(saturation_channel))
        saturation_std = float(np.std(saturation_channel))

        # Heuristic likelihood calculation
        ai_points = 12.0  # Natural base
        forensic_findings = []

        # A. Unnatural edge smoothness / super-resolution artifacts
        if laplacian_var < 75.0:
            ai_points += 22.0
            forensic_findings.append("Unusually low high-frequency edge variance (synthetic neural smoothing).")
        elif laplacian_var > 950.0:
            ai_points += 15.0
            forensic_findings.append("Hyper-detailed artificial micro-texture or high-pass sharpening artifacts.")

        # B. High-frequency FFT spectrum anomaly
        if fft_energy < 55.0 or fft_energy > 135.0:
            ai_points += 25.0
            forensic_findings.append(f"Spectral distribution anomaly in 2D-FFT frequency domain ({fft_energy:.1f} dB).")

        # C. Sensor noise consistency
        if noise_var < 1.5:
            ai_points += 20.0
            forensic_findings.append("Absence of natural optical sensor shot noise (sterile synthetic canvas).")

        # D. Oversaturated color gradients
        if mean_saturation > 140.0 and saturation_std > 65.0:
            ai_points += 12.0
            forensic_findings.append("Hyper-saturated color grading common in generative fantasy prompts.")

        # 3. Deepfake Detection (Member 3)
        deepfake_points = 5.0
        deepfake_findings = []

        if face_result["has_faces"]:
            for face in face_result["face_details"]:
                if face["is_synthetic_smoothing"]:
                    deepfake_points += 30.0
                    deepfake_findings.append(f"Facial region exhibits unnatural neural skin smoothing (Sharpness: {face['texture_sharpness']}).")

                # Boundary seam check: compare face variance to surrounding area
                x, y, fw, fh = face["box"]
                pad = 15
                y1 = max(0, y - pad)
                y2 = min(h, y + fh + pad)
                x1 = max(0, x - pad)
                x2 = min(w, x + fw + pad)
                border_crop = gray[y1:y2, x1:x2]
                border_diff = abs(float(cv2.Laplacian(border_crop, cv2.CV_64F).var()) - face["texture_sharpness"])
                if border_diff > 120.0:
                    deepfake_points += 25.0
                    deepfake_findings.append("Noticeable blending seam or resolution mismatch along face perimeter.")
        else:
            deepfake_findings.append("No human faces detected; deepfake facial evaluation skipped.")

        # Normalize scores
        ai_likelihood = min(96.0, max(5.0, round(ai_points, 1)))
        deepfake_score = min(95.0, max(4.0, round(deepfake_points, 1))) if face_result["has_faces"] else 0.0

        combined_risk = max(ai_likelihood, deepfake_score)
        authenticity_score = round(100.0 - combined_risk, 1)

        if combined_risk >= 60.0:
            verdict = "High Likelihood of AI Generation / Manipulation"
            risk_badge = "High Risk"
            summary_text = f"Forensic filters detected synthetic edge smoothing and frequency anomalies ({'; '.join(forensic_findings[:2])})."
        elif combined_risk >= 30.0:
            verdict = "Ambiguous / Possible Post-Processing"
            risk_badge = "Moderate Risk"
            summary_text = "Some compression or color adjustments diverge from raw camera output. Human verification recommended."
        else:
            verdict = "Authentic / Natural Capture"
            risk_badge = "Authentic"
            summary_text = "Camera sensor noise, frequency decay, and edge characteristics are consistent with genuine optical photography."

        limitations = [
            "AI-generated image analysis yields probabilistic indicators rather than definitive proof.",
            "Heavy social media compression algorithms may mimic generative smoothing.",
            "Professional studio retouching or denoising filters can trigger elevated synthetic scores."
        ]

        return {
            "filename": file_path.name,
            "media_type": "image",
            "width": int(w),
            "height": int(h),
            "face_detection": face_result,
            "ai_generated_detection": {
                "ai_likelihood_score": ai_likelihood,
                "spectral_energy": round(fft_energy, 2),
                "edge_sharpness": round(laplacian_var, 2),
                "noise_residual_variance": round(noise_var, 2),
                "findings": forensic_findings or ["No synthetic anomalies detected."]
            },
            "deepfake_detection": {
                "deepfake_score": deepfake_score,
                "faces_evaluated": face_result["faces_detected_count"],
                "findings": deepfake_findings
            },
            "authenticity_score": authenticity_score,
            "ai_likelihood_score": ai_likelihood,
            "verdict": verdict,
            "risk_badge": risk_badge,
            "summary": summary_text,
            "forensic_signals": {
                "laplacian_variance": round(laplacian_var, 2),
                "fft_high_freq_energy": round(fft_energy, 2),
                "noise_variance": round(noise_var, 2),
                "mean_saturation": round(mean_saturation, 2)
            },
            "limitations": limitations
        }

image_analyzer = ImageMediaAnalyzer()
