import re
from typing import Dict, Any, List, Optional

class ContentSafetyAnalyzer:
    """
    Member 4 - Content Analyzer.
    Provides:
    - Spam Detection
    - Toxic Comments Detection
    - Hate Speech Detection
    - NSFW Detection
    """

    SPAM_PATTERNS = [
        (r"(?:click\s+(?:here|link)|check\s+(?:out\s+)?my\s+bio)", 25.0, "Call-to-action link bait"),
        (r"(?:t\.me\/|telegram|wa\.me\/|whatsapp\s+me|dm\s+(?:me\s+)?(?:on\s+)?(?:insta|ig))", 30.0, "Off-platform redirect"),
        (r"(?:make\s+money\s+online|earn\s+\$\d+|passive\s+income|guaranteed\s+(?:profit|return))", 35.0, "Financial scam / get-rich-quick phrase"),
        (r"(?:crypto|bitcoin|binance|forex|usdt|airdrop|token\s+presale)", 25.0, "Cryptocurrency promotion"),
        (r"(?:free\s+(?:followers|likes|views|v-?bucks|gift\s*card))", 30.0, "Engagement farming scam"),
        (r"(?:limited\s+time\s+offer|act\s+fast|exclusive\s+deal|use\s+code\s+[A-Z0-9]+)", 20.0, "High-pressure commercial marketing"),
        (r"(?:https?:\/\/(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|cutt\.ly)\/[a-zA-Z0-9]+)", 25.0, "Obfuscated shortlink URL")
    ]

    TOXIC_TERMS = {
        "profanity": ["fuck", "shit", "bitch", "asshole", "bastard", "crap", "dick", "piss"],
        "insult": ["idiot", "moron", "loser", "stupid", "pathetic", "dumb", "clown", "trash", "scum", "ugly"],
        "threat": ["kill yourself", "die", "punch you", "beat you", "destroy you", "slit your", "burn in hell"]
    }

    HATE_SPEECH_PATTERNS = [
        (r"\b(?:nigg[aer]|chink|kike|faggot|dyke|retard|spic|tranny)\b", 80.0, "Racial / Sexual Orientation Slur"),
        (r"\b(?:go\s+back\s+to\s+your\s+country|illegal\s+alien\s+invaders|subhuman)\b", 70.0, "Xenophobic / Dehumanizing rhetoric"),
        (r"\b(?:all\s+(?:jews|muslims|christians|blacks|whites|asians)\s+are\s+(?:evil|terrorists|criminals|parasites))\b", 85.0, "Targeted Religious / Ethnic Hate")
    ]

    NSFW_TERMS = [
        (r"\b(?:porn|pornography|xxx|hentai|onlyfans|fansly|nude|nudes|naked|sex|sexy\s+cam)\b", 60.0, "Adult Content / Nudity"),
        (r"\b(?:escort|hookup|sugar\s*daddy|sugar\s*baby|pay\s+for\s+play|erotic\s+massage)\b", 55.0, "Adult Solicitation"),
        (r"\b(?:beheading|gore|decapitation|mutilation|snuff|bloodbath)\b", 75.0, "Graphic Violence / Gore")
    ]

    def __init__(self):
        self.spam_compiled = [(re.compile(p, re.I), score, desc) for p, score, desc in self.SPAM_PATTERNS]
        self.hate_compiled = [(re.compile(p, re.I), score, cat) for p, score, cat in self.HATE_SPEECH_PATTERNS]
        self.nsfw_compiled = [(re.compile(p, re.I), score, cat) for p, score, cat in self.NSFW_TERMS]

    def detect_spam(self, text: str) -> Dict[str, Any]:
        score = 0.0
        reasons = []
        flagged_patterns = []

        # 1. Pattern matching
        for pattern, pts, desc in self.spam_compiled:
            match = pattern.search(text)
            if match:
                score += pts
                reasons.append(desc)
                flagged_patterns.append(match.group(0))

        # 2. Repeated characters / shouting
        caps_count = sum(1 for c in text if c.isupper())
        total_letters = sum(1 for c in text if c.isalpha())
        if total_letters > 15 and (caps_count / total_letters) > 0.65:
            score += 15.0
            reasons.append("Excessive uppercase lettering (shouting)")

        if re.search(r"(!|\?|\$){4,}", text):
            score += 10.0
            reasons.append("Excessive repeated punctuation")

        # 3. Repeated identical words
        words = text.lower().split()
        if len(words) > 6:
            word_freq = {}
            for w in words:
                word_freq[w] = word_freq.get(w, 0) + 1
            max_repeat = max(word_freq.values())
            if max_repeat / len(words) > 0.35:
                score += 20.0
                reasons.append("High repetitive word frequency (flooding)")

        final_score = min(100.0, max(0.0, round(score, 1)))
        is_spam = final_score >= 35.0

        return {
            "is_spam": is_spam,
            "spam_score": final_score,
            "confidence": "High" if final_score > 60 else "Moderate" if is_spam else "Low",
            "reasons": reasons or ["No promotional or spam triggers detected."],
            "flagged_patterns": flagged_patterns
        }

    def detect_toxicity(self, text: str) -> Dict[str, Any]:
        lower_text = text.lower()
        score = 0.0
        flagged = []
        subcategories = {"profanity": 0.0, "insult": 0.0, "threat": 0.0}

        # Check threat phrases
        for threat in self.TOXIC_TERMS["threat"]:
            if threat in lower_text:
                score += 45.0
                subcategories["threat"] += 45.0
                flagged.append(threat)

        # Check insults
        for insult in self.TOXIC_TERMS["insult"]:
            if re.search(r"\b" + re.escape(insult) + r"\b", lower_text):
                score += 20.0
                subcategories["insult"] += 20.0
                flagged.append(insult)

        # Check profanity
        for prof in self.TOXIC_TERMS["profanity"]:
            if re.search(r"\b" + re.escape(prof) + r"\b", lower_text):
                score += 15.0
                subcategories["profanity"] += 15.0
                flagged.append(prof)

        final_score = min(100.0, max(0.0, round(score, 1)))
        is_toxic = final_score >= 25.0

        severity = "Severe" if final_score >= 60 else "Moderate" if is_toxic else "None"

        return {
            "is_toxic": is_toxic,
            "toxicity_score": final_score,
            "severity": severity,
            "flagged_tokens": flagged,
            "subcategories": {k: min(100.0, v) for k, v in subcategories.items()}
        }

    def detect_hate_speech(self, text: str) -> Dict[str, Any]:
        score = 0.0
        targeted = []
        flagged_terms = []

        for pattern, pts, category in self.hate_compiled:
            match = pattern.search(text)
            if match:
                score += pts
                targeted.append(category)
                flagged_terms.append(match.group(0))

        final_score = min(100.0, max(0.0, round(score, 1)))
        is_hate = final_score >= 40.0
        severity = "Critical" if final_score >= 70 else "High" if is_hate else "None"

        return {
            "is_hate_speech": is_hate,
            "hate_speech_score": final_score,
            "severity": severity,
            "targeted_categories": list(set(targeted)),
            "flagged_terms": flagged_terms
        }

    def detect_nsfw(self, text: str) -> Dict[str, Any]:
        score = 0.0
        content_types = []
        flagged_terms = []

        for pattern, pts, category in self.nsfw_compiled:
            match = pattern.search(text)
            if match:
                score += pts
                content_types.append(category)
                flagged_terms.append(match.group(0))

        final_score = min(100.0, max(0.0, round(score, 1)))
        is_nsfw = final_score >= 35.0
        severity = "Explicit" if final_score >= 60 else "Suggestive" if is_nsfw else "Safe"

        return {
            "is_nsfw": is_nsfw,
            "nsfw_score": final_score,
            "severity": severity,
            "content_types": list(set(content_types)),
            "flagged_terms": flagged_terms
        }

    def analyze(self, text: str, author_username: Optional[str] = None, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes full Member 4 Content Analysis:
        - Spam
        - Toxic Comments
        - Hate Speech
        - NSFW
        """
        spam_res = self.detect_spam(text)
        toxic_res = self.detect_toxicity(text)
        hate_res = self.detect_hate_speech(text)
        nsfw_res = self.detect_nsfw(text)

        # Composite Threat Level
        max_threat = max(
            spam_res["spam_score"],
            toxic_res["toxicity_score"],
            hate_res["hate_speech_score"] * 1.2,  # Weighted higher
            nsfw_res["nsfw_score"]
        )
        max_threat = min(100.0, max_threat)
        overall_safety = round(100.0 - max_threat, 1)

        if max_threat >= 70.0 or hate_res["is_hate_speech"]:
            verdict = "Severe Violation / Harmful Content"
            verdict_badge = "High Risk"
            threat_level = "Critical Threat"
            recommendation = "Automatically block or delete. Content violates platform safety guidelines."
        elif max_threat >= 35.0:
            verdict = "Questionable / Potential Violation"
            verdict_badge = "Moderate Risk"
            threat_level = "Moderate Threat"
            recommendation = "Hold for human moderator inspection. Flags detected for review."
        else:
            verdict = "Safe / Compliant Content"
            verdict_badge = "Safe"
            threat_level = "Clean"
            recommendation = "Content meets standard community safety standards."

        summary_parts = []
        if spam_res["is_spam"]:
            summary_parts.append(f"Spam detected ({spam_res['spam_score']}%)")
        if toxic_res["is_toxic"]:
            summary_parts.append(f"Toxicity detected ({toxic_res['toxicity_score']}%)")
        if hate_res["is_hate_speech"]:
            summary_parts.append(f"Hate Speech flagged ({hate_res['hate_speech_score']}%)")
        if nsfw_res["is_nsfw"]:
            summary_parts.append(f"NSFW flagged ({nsfw_res['nsfw_score']}%)")

        summary = "; ".join(summary_parts) if summary_parts else "Clean content with no policy or security violations."

        return {
            "text_length": len(text),
            "analyzed_text_sample": text[:120] + ("..." if len(text) > 120 else ""),
            "author_username": author_username,
            "context": context or "comment",
            "overall_safety_score": overall_safety,
            "threat_level": threat_level,
            "verdict": verdict,
            "verdict_badge": verdict_badge,
            "summary": summary,
            "spam_detection": spam_res,
            "toxic_comments": toxic_res,
            "hate_speech_detection": hate_res,
            "nsfw_detection": nsfw_res,
            "action_recommendation": recommendation
        }

content_safety_analyzer = ContentSafetyAnalyzer()
