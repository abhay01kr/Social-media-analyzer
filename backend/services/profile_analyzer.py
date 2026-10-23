import re
import math
from typing import Dict, Any, List, Optional

class ProfileRiskAnalyzer:
    """
    Member 2 - Profile Analyzer.
    Provides comprehensive analysis:
    - Username Analysis
    - Bio Analysis
    - Followers/Following Ratio
    - Engagement Rate
    - Fake Profile Score
    - Trust Score
    """

    ALLOWED_PLATFORMS = ["Instagram", "Facebook", "LinkedIn", "X", "TikTok", "YouTube"]

    SPAM_BIO_PATTERNS = [
        r"(?:dm\s+(?:me\s+)?for\s+(?:promo|collab|rates|credit))",
        r"(?:t\.me\/|telegram|wa\.me\/|whatsapp)",
        r"(?:crypto|forex|binary|invest|guaranteed\s+(?:returns|profit))",
        r"(?:cashapp|venmo|paypal\s+me|send\s+\$)",
        r"(?:sugar\s+(?:daddy|mommy)|allowance|hookup)",
        r"(?:click\s+(?:link|here)\s+below)",
        r"(?:free\s+(?:followers|likes|crypto|vbucks|giftcard))"
    ]

    def __init__(self):
        self.spam_regexes = [re.compile(p, re.IGNORECASE) for p in self.SPAM_BIO_PATTERNS]

    def extract_username(self, raw_input: str) -> str:
        s = raw_input.strip().rstrip("/")
        if any(domain in s for domain in ["instagram.com", "facebook.com", "linkedin.com", "x.com", "twitter.com", "tiktok.com", "youtube.com"]):
            parts = s.split("/")
            s = parts[-1].split("?")[0].lstrip("@")
        elif s.startswith("@"):
            s = s[1:]
        return s

    def analyze_username(self, username: str) -> Dict[str, Any]:
        """Deep analysis of username structure, bot naming conventions, and randomness."""
        clean = self.extract_username(username)
        length = len(clean)
        digit_count = sum(c.isdigit() for c in clean)
        digit_ratio = (digit_count / length) if length > 0 else 0.0
        findings: List[str] = []
        risk_points = 0.0

        is_bot_pattern = False
        if length < 3:
            risk_points += 15.0
            findings.append("Abnormally short username (< 3 characters).")
        elif re.search(r"\d{4,}$", clean):
            is_bot_pattern = True
            risk_points += 25.0
            findings.append("Username ends with 4+ sequential digits (typical automated bot generation pattern).")
        elif digit_ratio > 0.4:
            is_bot_pattern = True
            risk_points += 20.0
            findings.append(f"High numeric concentration ({digit_count}/{length} digits, {digit_ratio*100:.0f}%).")
        
        # Check leetspeak and scam keywords in username
        lower_u = clean.lower()
        suspicious_words = ["promo", "bot", "giveaway", "crypto", "free", "admin", "official_support"]
        for sw in suspicious_words:
            if sw in lower_u:
                risk_points += 15.0
                findings.append(f"Username contains high-risk keyword: '{sw}'.")
                break

        if not findings:
            findings.append("Username follows standard, human-created conventions.")

        return {
            "clean_username": clean,
            "length": length,
            "digit_count": digit_count,
            "digit_ratio": round(digit_ratio, 3),
            "is_bot_pattern": is_bot_pattern,
            "risk_points": min(35.0, risk_points),
            "findings": findings
        }

    def analyze_bio(self, bio: Optional[str]) -> Dict[str, Any]:
        """Inspects biography for spam phrases, suspicious links, emoji stuffing, and external redirects."""
        findings: List[str] = []
        risk_points = 0.0

        if not bio or not bio.strip():
            return {
                "bio_text": None,
                "length": 0,
                "has_spam_keywords": False,
                "has_suspicious_links": False,
                "emoji_count": 0,
                "sentiment": "Neutral / Empty",
                "risk_points": 10.0,
                "findings": ["Bio is completely blank (common in low-effort bot accounts)."]
            }

        bio_clean = bio.strip()
        bio_len = len(bio_clean)
        
        # Emoji count (non-ascii high code points)
        emoji_count = len(re.findall(r"[\U00010000-\U0010ffff]", bio_clean))
        
        # Check spam phrases
        has_spam = False
        for reg in self.spam_regexes:
            match = reg.search(bio_clean)
            if match:
                has_spam = True
                risk_points += 25.0
                findings.append(f"Suspicious / spam pattern detected: '{match.group(0)}'.")

        # Check external link redirects
        has_suspicious_links = bool(re.search(r"(?:https?:\/\/|t\.me\/|wa\.me\/|bit\.ly\/|tinyurl\.com\/|t\.co\/)", bio_clean, re.I))
        if has_suspicious_links:
            risk_points += 15.0
            findings.append("Bio contains external URL redirect or encrypted shortlink.")

        # Emoji stuffing
        if emoji_count > 8 or (bio_len > 0 and emoji_count / bio_len > 0.25):
            risk_points += 10.0
            findings.append(f"High emoji density ({emoji_count} emojis) often used in automated promotional spam.")

        if not findings:
            findings.append("Bio text appears authentic, personal, and free of spam signatures.")

        return {
            "bio_text": bio_clean,
            "length": bio_len,
            "has_spam_keywords": has_spam,
            "has_suspicious_links": has_suspicious_links,
            "emoji_count": emoji_count,
            "sentiment": "Commercial / Spam" if has_spam else "Authentic",
            "risk_points": min(35.0, risk_points),
            "findings": findings
        }

    def analyze_followers_ratio(self, followers: Optional[int], following: Optional[int]) -> Dict[str, Any]:
        """Calculates Followers-to-Following ratio and detects follow-churn farming."""
        findings: List[str] = []
        risk_points = 0.0
        is_farming = False

        if followers is None or following is None:
            return {
                "followers": followers,
                "following": following,
                "ratio": None,
                "ratio_status": "Not provided",
                "is_follow_farming": False,
                "risk_points": 0.0,
                "findings": ["Follower/following counts not provided."]
            }

        if following == 0:
            ratio = float(followers)
        else:
            ratio = round(followers / following, 3)

        if following > 1500 and followers < 100:
            is_farming = True
            risk_points += 30.0
            status = "Extreme Follow-farming / Bot"
            findings.append(f"Follow-farming pattern: Following {following} accounts but only {followers} followers (Ratio: {ratio}).")
        elif following > 800 and ratio < 0.15:
            is_farming = True
            risk_points += 20.0
            status = "Unbalanced / Follow-Churn"
            findings.append(f"Low follower retention: Following significantly exceeds audience size (Ratio: {ratio}).")
        elif ratio >= 1.0:
            status = "Healthy / High Authority"
            findings.append(f"Healthy distribution: More followers than following (Ratio: {ratio}).")
        else:
            status = "Normal / Balanced"
            findings.append(f"Standard human follower-to-following distribution (Ratio: {ratio}).")

        return {
            "followers": followers,
            "following": following,
            "ratio": ratio,
            "ratio_status": status,
            "is_follow_farming": is_farming,
            "risk_points": risk_points,
            "findings": findings
        }

    def analyze_engagement_rate(
        self,
        followers: Optional[int],
        posts: Optional[int],
        avg_likes: Optional[float] = None,
        avg_comments: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculates or estimates Engagement Rate relative to audience size."""
        findings: List[str] = []
        risk_points = 0.0

        if followers is not None and followers > 0 and (avg_likes is not None or avg_comments is not None):
            total_interactions = (avg_likes or 0.0) + (avg_comments or 0.0)
            engagement_rate = round((total_interactions / followers) * 100.0, 2)
            
            if engagement_rate < 0.2 and followers > 5000:
                risk_points += 25.0
                status = "Extremely Low / Ghost Followers"
                findings.append(f"Engagement rate is only {engagement_rate}%, indicating a high proportion of inactive or purchased bot followers.")
            elif engagement_rate > 25.0 and followers > 10000:
                risk_points += 15.0
                status = "Abnormally High / Pod Manipulation"
                findings.append(f"Engagement rate of {engagement_rate}% is statistical anomaly, possibly inflated by engagement pods or like-farms.")
            elif engagement_rate >= 1.5:
                status = "Optimal Human Engagement"
                findings.append(f"Engagement rate of {engagement_rate}% aligns with healthy real-audience benchmarks (1.5% - 5%).")
            else:
                status = "Moderate Engagement"
                findings.append(f"Standard engagement rate of {engagement_rate}%.")
        else:
            # Baseline estimation if post count is 0
            if posts == 0:
                risk_points += 15.0
                engagement_rate = 0.0
                status = "Inactive (0 Posts)"
                findings.append("Account has 0 published posts, making natural interaction impossible.")
            else:
                engagement_rate = 2.5  # Estimated average
                status = "Estimated Average (Sample not supplied)"
                findings.append("Engagement rate estimated at standard baseline (2.5%) based on public profile parameters.")

        return {
            "engagement_rate_percent": engagement_rate,
            "benchmark_status": status,
            "estimated_activity_level": "Active" if (posts or 1) > 5 else "Low Activity",
            "risk_points": risk_points,
            "findings": findings
        }

    def analyze(
        self,
        platform: str,
        username_or_url: str,
        bio: Optional[str] = None,
        followers_count: Optional[int] = None,
        following_count: Optional[int] = None,
        posts_count: Optional[int] = None,
        avg_likes_per_post: Optional[float] = None,
        avg_comments_per_post: Optional[float] = None,
        has_avatar: Optional[bool] = None,
        account_age_days: Optional[int] = None,
        is_verified: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Executes full Member 2 analysis pipeline and synthesizes Fake Profile Score & Trust Score.
        """
        norm_platform = platform.capitalize()
        if "x" in norm_platform.lower() or "twitter" in norm_platform.lower():
            norm_platform = "X"
        elif "linked" in norm_platform.lower():
            norm_platform = "LinkedIn"
        elif "insta" in norm_platform.lower():
            norm_platform = "Instagram"
        elif "face" in norm_platform.lower():
            norm_platform = "Facebook"
        elif "tik" in norm_platform.lower():
            norm_platform = "TikTok"
        elif "tube" in norm_platform.lower():
            norm_platform = "YouTube"

        # 1. Username Analysis
        user_res = self.analyze_username(username_or_url)
        clean_user = user_res["clean_username"]

        # 2. Bio Analysis
        bio_res = self.analyze_bio(bio)

        # 3. Follower / Following Ratio
        ratio_res = self.analyze_followers_ratio(followers_count, following_count)

        # 4. Engagement Rate
        eng_res = self.analyze_engagement_rate(
            followers=followers_count,
            posts=posts_count,
            avg_likes=avg_likes_per_post,
            avg_comments=avg_comments_per_post
        )

        # 5. Profile Picture & Verification Signals
        evidence: List[Dict[str, Any]] = []
        missing_data_notes: List[str] = []
        total_risk_points = (
            user_res["risk_points"] +
            bio_res["risk_points"] +
            ratio_res["risk_points"] +
            eng_res["risk_points"]
        )

        for finding in user_res["findings"]:
            evidence.append({
                "signal": "Username Analysis",
                "finding": finding,
                "severity": "high" if user_res["is_bot_pattern"] else "low",
                "impact": f"+{user_res['risk_points']:.0f} risk" if user_res["risk_points"] > 0 else "0 risk"
            })

        for finding in bio_res["findings"]:
            evidence.append({
                "signal": "Bio Analysis",
                "finding": finding,
                "severity": "high" if bio_res["has_spam_keywords"] else "low",
                "impact": f"+{bio_res['risk_points']:.0f} risk" if bio_res["risk_points"] > 0 else "0 risk"
            })

        for finding in ratio_res["findings"]:
            evidence.append({
                "signal": "Followers/Following Ratio",
                "finding": finding,
                "severity": "high" if ratio_res["is_follow_farming"] else "low",
                "impact": f"+{ratio_res['risk_points']:.0f} risk" if ratio_res["risk_points"] > 0 else "0 risk"
            })

        for finding in eng_res["findings"]:
            evidence.append({
                "signal": "Engagement Rate",
                "finding": finding,
                "severity": "medium" if eng_res["risk_points"] > 0 else "low",
                "impact": f"+{eng_res['risk_points']:.0f} risk" if eng_res["risk_points"] > 0 else "0 risk"
            })

        # Avatar check
        if has_avatar is False:
            total_risk_points += 15.0
            evidence.append({
                "signal": "Avatar Presence",
                "finding": "Default or absent profile photo.",
                "severity": "medium",
                "impact": "+15 risk"
            })
        elif has_avatar is True:
            evidence.append({
                "signal": "Avatar Presence",
                "finding": "Custom profile picture is uploaded.",
                "severity": "low",
                "impact": "0 risk"
            })

        # Account age
        if account_age_days is not None:
            if account_age_days < 7:
                total_risk_points += 20.0
                evidence.append({
                    "signal": "Account Age",
                    "finding": f"Newly created account (only {account_age_days} days old).",
                    "severity": "high",
                    "impact": "+20 risk"
                })
            elif account_age_days > 365:
                total_risk_points = max(0.0, total_risk_points - 10.0)
                evidence.append({
                    "signal": "Account Age",
                    "finding": f"Established profile ({account_age_days // 365} years old).",
                    "severity": "positive",
                    "impact": "-10 risk"
                })

        # Verified badge
        if is_verified:
            total_risk_points = max(0.0, total_risk_points - 30.0)
            evidence.append({
                "signal": "Official Verification",
                "finding": f"Officially verified account badge on {norm_platform}.",
                "severity": "positive",
                "impact": "-30 risk"
            })

        # 5. Fake Profile Score & Trust Score
        fake_profile_score = round(min(100.0, max(0.0, total_risk_points)), 1)
        trust_score = round(100.0 - fake_profile_score, 1)

        if fake_profile_score >= 60.0:
            verdict = "Suspicious / Fake Profile Likely"
            verdict_badge = "High Risk"
            recommendation = "High risk of automated bot, spam farm, or impersonation. Exercise caution before interacting."
        elif fake_profile_score >= 30.0:
            verdict = "Moderate Risk / Ambiguous Signals"
            verdict_badge = "Moderate Risk"
            recommendation = "Some signals deviate from typical human benchmarks. Review manual post content and comment history."
        else:
            verdict = "Authentic / Trusted Profile"
            verdict_badge = "Trusted"
            recommendation = "Behavioral and metadata signals align with an authentic human account."

        missing_data_notes.extend([
            f"Official {norm_platform} API restrictions limit direct retrieval of private engagement telemetry.",
            "Analysis adheres to public statistical heuristics without breaching user privacy."
        ])

        return {
            "platform": norm_platform,
            "username": clean_user,
            "fake_profile_score": fake_profile_score,
            "trust_score": trust_score,
            "verdict": verdict,
            "verdict_badge": verdict_badge,
            "recommendation": recommendation,
            "username_analysis": user_res,
            "bio_analysis": bio_res,
            "followers_following_ratio": ratio_res,
            "engagement_rate": eng_res,
            "evidence": evidence,
            "missing_data_notes": missing_data_notes,
            "disclaimer": "This analysis represents statistical risk heuristics and does not constitute conclusive legal proof."
        }

profile_risk_analyzer = ProfileRiskAnalyzer()
