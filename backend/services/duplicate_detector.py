import cv2
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from config import REFERENCE_DIR

class DuplicateDetector:
    """
    Video duplicate and reuse checker using Perceptual Hashing (dHash).
    Follows project requirements:
    - Compares sampled frames/perceptual fingerprints against a reference set.
    - Similarity result ONLY when comparison data exists.
    - Accurately reports absence of comparison data when database is empty.
    """

    def __init__(self, reference_dir: Optional[Path] = None):
        self.reference_dir = reference_dir or REFERENCE_DIR
        self.reference_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.reference_dir / "index.json"
        self._ensure_index()

    def _ensure_index(self):
        if not self.index_file.exists():
            with open(self.index_file, "w") as f:
                json.dump({"references": []}, f, indent=2)

    def compute_dhash(self, frame: np.ndarray, hash_size: int = 8) -> str:
        """Computes a difference hash (dHash) for a single frame."""
        if frame is None or frame.size == 0:
            return "0" * (hash_size * hash_size // 4)
        
        # Convert to grayscale if not already
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Resize to (hash_size + 1, hash_size)
        resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)

        # Compare adjacent pixels
        diff = resized[:, 1:] > resized[:, :-1]
        
        # Convert boolean array to hex string
        decimal_val = 0
        for val in diff.flatten():
            decimal_val = (decimal_val << 1) | int(val)
        
        hex_len = (hash_size * hash_size) // 4
        return f"{decimal_val:0{hex_len}x}"

    def hamming_distance(self, hex_hash1: str, hex_hash2: str) -> int:
        """Calculates bit difference between two hex perceptual hashes."""
        try:
            val1 = int(hex_hash1, 16)
            val2 = int(hex_hash2, 16)
            xor = val1 ^ val2
            return bin(xor).count("1")
        except Exception:
            return 64

    def generate_fingerprint(self, sampled_frames: List[Tuple[int, np.ndarray]]) -> List[Dict[str, Any]]:
        fingerprints = []
        for idx, frame in sampled_frames:
            h = self.compute_dhash(frame)
            fingerprints.append({
                "frame_index": idx,
                "dhash": h
            })
        return fingerprints

    def add_reference(self, reference_id: str, title: str, fingerprints: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None):
        with open(self.index_file, "r") as f:
            data = json.load(f)

        # Remove existing if same ID
        data["references"] = [r for r in data["references"] if r.get("id") != reference_id]
        data["references"].append({
            "id": reference_id,
            "title": title,
            "fingerprints": fingerprints,
            "metadata": metadata or {}
        })

        with open(self.index_file, "w") as f:
            json.dump(data, f, indent=2)

    def check_duplicate(self, sampled_frames: List[Tuple[int, np.ndarray]]) -> Dict[str, Any]:
        """
        Compares query video frames against reference set.
        Returns match results if reference data exists; otherwise clarifies no comparison data exists.
        """
        with open(self.index_file, "r") as f:
            data = json.load(f)

        references = data.get("references", [])
        query_fps = self.generate_fingerprint(sampled_frames)

        if not references:
            return {
                "comparison_data_exists": False,
                "similarity_score": None,
                "is_duplicate": False,
                "matches": [],
                "reference_count": 0,
                "query_fingerprints_count": len(query_fps),
                "notes": "No reference videos exist in database. Register reference media to enable duplicate matching."
            }

        best_match = None
        highest_similarity = 0.0
        matches = []

        query_hashes = [f["dhash"] for f in query_fps]

        for ref in references:
            ref_hashes = [f["dhash"] for f in ref.get("fingerprints", [])]
            if not ref_hashes or not query_hashes:
                continue

            # Compare sampled frame hashes
            matched_pairs = 0
            total_checks = min(len(query_hashes), len(ref_hashes))
            
            for q_h in query_hashes:
                min_dist = min(self.hamming_distance(q_h, r_h) for r_h in ref_hashes)
                # If Hamming distance <= 10 out of 64 bits, consider frame matched
                if min_dist <= 10:
                    matched_pairs += 1

            similarity = round((matched_pairs / max(1, len(query_hashes))) * 100, 1)

            if similarity >= 50.0:
                matches.append({
                    "reference_id": ref.get("id"),
                    "title": ref.get("title"),
                    "similarity_percent": similarity,
                    "matched_frames": matched_pairs
                })

            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = ref

        is_duplicate = highest_similarity >= 75.0

        return {
            "comparison_data_exists": True,
            "similarity_score": highest_similarity,
            "is_duplicate": is_duplicate,
            "matches": matches,
            "reference_count": len(references),
            "query_fingerprints_count": len(query_fps),
            "verdict": "High Reuse Detected" if is_duplicate else ("Potential Partial Reuse" if highest_similarity >= 40 else "Unique / No Match"),
            "notes": f"Evaluated against {len(references)} reference video fingerprint(s)."
        }

duplicate_detector = DuplicateDetector()
