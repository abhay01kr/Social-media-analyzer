import cv2
import numpy as np
from typing import Dict, Any, List

class FaceDetectorService:
    """
    Member 3 - Face Detection Service.
    Robust multi-version detector supporting OpenCV 4.x and OpenCV 5.x.
    Uses Haar cascades if available, and high-accuracy skin chrominance + geometric aspect ratio analysis.
    """

    def __init__(self):
        self._has_cascade = hasattr(cv2, "CascadeClassifier")
        self.cascade = None
        if self._has_cascade:
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self.cascade = cv2.CascadeClassifier(cascade_path)
            except Exception:
                self.cascade = None

    def _detect_faces_chroma(self, image: np.ndarray) -> List[Dict[str, int]]:
        """
        Detects faces using YCrCb skin-color distribution and face aspect ratio geometry.
        In YCrCb space, human skin colors are constrained to:
        133 <= Cr <= 173, 77 <= Cb <= 127
        """
        h_img, w_img = image.shape[:2]
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        
        # Skin color mask in YCrCb space
        lower_skin = np.array([0, 133, 77], dtype=np.uint8)
        upper_skin = np.array([255, 173, 127], dtype=np.uint8)
        mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

        # Morphological operations to clean up noise and close holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        min_area = (w_img * h_img) * 0.015  # At least 1.5% of total image

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(h) / float(w)
                # Human face aspect ratio is typically between 1.05 and 1.95
                if 0.95 <= aspect_ratio <= 2.2:
                    boxes.append((x, y, w, h))

        return boxes

    def detect_faces(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detects faces in a BGR image array.
        Returns face count, bounding boxes [x, y, w, h], and face details.
        """
        if image is None or image.size == 0:
            return {
                "faces_detected_count": 0,
                "has_faces": False,
                "bounding_boxes": [],
                "face_details": []
            }

        h_img, w_img = image.shape[:2]
        raw_boxes = []

        # Try cascade if available and loaded
        if self.cascade is not None and not self.cascade.empty():
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
                equalized = cv2.equalizeHist(gray)
                faces = self.cascade.detectMultiScale(equalized, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                raw_boxes = [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
            except Exception:
                raw_boxes = []

        # If cascade not available or detected 0 faces, try skin chrominance segmentation
        if not raw_boxes and len(image.shape) == 3:
            raw_boxes = self._detect_faces_chroma(image)

        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        boxes = []
        face_details = []

        for (x, y, w, h) in raw_boxes:
            boxes.append({
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "relative_area_percent": round(((w * h) / (w_img * h_img)) * 100, 2)
            })

            face_roi = gray_img[y:y+h, x:x+w]
            laplacian_var = float(cv2.Laplacian(face_roi, cv2.CV_64F).var()) if face_roi.size > 0 else 0.0

            face_details.append({
                "box": [int(x), int(y), int(w), int(h)],
                "texture_sharpness": round(laplacian_var, 2),
                "is_synthetic_smoothing": laplacian_var < 45.0
            })

        return {
            "faces_detected_count": len(boxes),
            "has_faces": len(boxes) > 0,
            "bounding_boxes": boxes,
            "face_details": face_details
        }

face_detector = FaceDetectorService()
