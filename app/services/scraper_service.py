import httpx
from app.config import settings
from typing import List, Dict
from datetime import datetime

ATTACK_KEYWORDS_ENGLISH = [
    "lied", "corrupt", "corruption", "fake",
    "deceived", "deceive", "thief", "stole",
    "stealing", "fraud", "fraudster", "criminal",
    "betrayed", "traitor", "failure", "failed",
    "useless", "worthless", "incompetent",
    "abandoned", "empty promises", "do nothing",
    "party jumper", "desperate", "loser",
    "puppet", "illegal", "nothing to show",
]

ATTACK_KEYWORDS_HAUSA = [
    "karya", "munafiki", "barawo", "zamba",
    "cuta", "yaudara", "rashin aminci",
    "banza", "maƙarƙashiya", "gambara",
    "satar kuɗi", "ƙarya", "canjin jam'iyya",
    "bai cika alkawali ba", "bai yi komai ba",
]

CANDIDATE_NAMES = [
    "dahuwa", "ismaila dahuwa", "dr dahuwa",
    "dr. dahuwa", "dahuwa kaila",
    "senator dahuwa", "prp bauchi north",
    "bauchi north senator",
]


class ScraperService:

    def __init__(self):
        self.mention_key = settings.MENTION_API_KEY
        self.mention_account = (
            settings.MENTION_ACCOUNT_ID
        )

    async def get_recent_mentions(
        self, limit: int = 50
    ) -> List[Dict]:
        if not self.mention_key:
            return []
        try:
            async with httpx.AsyncClient(
                timeout=30
            ) as client:
                r = await client.get(
                    f"https://api.mention.net/api"
                    f"/accounts/"
                    f"{self.mention_account}/alerts",
                    headers={
                        "Authorization": (
                            f"Bearer {self.mention_key}"
                        )
                    },
                )
            data = r.json()
            alerts = data.get("alerts", [])
            all_mentions = []
            for alert in alerts[:3]:
                alert_id = alert.get("id")
                mentions = await (
                    self._get_alert_mentions(
                        alert_id, limit
                    )
                )
                all_mentions.extend(mentions)
            return all_mentions
        except Exception as e:
            print(f"Mention.com error: {e}")
            return []

    async def _get_alert_mentions(
        self, alert_id: str, limit: int
    ) -> List[Dict]:
        try:
            async with httpx.AsyncClient(
                timeout=30
            ) as client:
                r = await client.get(
                    f"https://api.mention.net/api"
                    f"/accounts/"
                    f"{self.mention_account}"
                    f"/alerts/{alert_id}/mentions",
                    headers={
                        "Authorization": (
                            f"Bearer {self.mention_key}"
                        )
                    },
                    params={"limit": limit},
                )
            return r.json().get("mentions", [])
        except Exception:
            return []

    async def scrape_google_news(
        self,
    ) -> List[Dict]:
        queries = [
            "Dr Ismaila Dahuwa",
            "Dahuwa Kaila Bauchi",
            "PRP Bauchi North senator",
        ]
        results = []
        async with httpx.AsyncClient(
            timeout=20
        ) as client:
            for query in queries:
                try:
                    url = (
                        f"https://news.google.com"
                        f"/rss/search?q="
                        f"{query.replace(' ', '+')}"
                        f"&hl=en-NG&gl=NG&ceid=NG:en"
                    )
                    r = await client.get(url)
                    items = r.text.split(
                        "<item>"
                    )[1:]
                    for item in items[:5]:
                        title = self._extract_xml(
                            item, "title"
                        )
                        link = self._extract_xml(
                            item, "link"
                        )
                        pub_date = self._extract_xml(
                            item, "pubDate"
                        )
                        description = (
                            self._extract_xml(
                                item, "description"
                            )
                        )
                        if title:
                            results.append({
                                "source": (
                                    "Google News"
                                ),
                                "title": title,
                                "url": link,
                                "published": pub_date,
                                "content": description,
                                "platform": "news",
                            })
                except Exception as e:
                    print(f"News error: {e}")
        return results

    def _extract_xml(
        self, text: str, tag: str
    ) -> str:
        try:
            start = text.find(
                f"<{tag}>"
            ) + len(f"<{tag}>")
            end = text.find(f"</{tag}>")
            if start > 0 and end > start:
                return text[start:end].strip()
        except Exception:
            pass
        return ""

    def analyze_for_attacks(
        self, content: str, source: str = ""
    ) -> Dict:
        content_lower = content.lower()

        mentions_candidate = any(
            name in content_lower
            for name in CANDIDATE_NAMES
        )
        if not mentions_candidate:
            return {
                "is_attack": False,
                "threat_level": "none",
                "reason": "Does not mention candidate",
            }

        english_hits = [
            kw for kw in ATTACK_KEYWORDS_ENGLISH
            if kw in content_lower
        ]
        hausa_hits = [
            kw for kw in ATTACK_KEYWORDS_HAUSA
            if kw in content_lower
        ]
        all_hits = english_hits + hausa_hits
        hit_count = len(all_hits)

        if hit_count == 0:
            return {
                "is_attack": False,
                "threat_level": "none",
                "keywords_found": [],
            }

        threat = (
            "CRITICAL" if hit_count >= 4
            else "HIGH" if hit_count >= 2
            else "MEDIUM"
        )

        attack_type = "general_attack"
        if any(k in content_lower for k in [
            "corrupt", "thief", "stole", "barawo",
            "satar kuɗi", "fraud"
        ]):
            attack_type = "corruption_allegation"
        elif any(k in content_lower for k in [
            "lied", "fake", "karya", "munafiki",
            "yaudara", "deceived"
        ]):
            attack_type = "integrity_attack"
        elif any(k in content_lower for k in [
            "party jumper", "canjin jam'iyya",
            "traitor", "betrayed"
        ]):
            attack_type = "party_loyalty_attack"
        elif any(k in content_lower for k in [
            "failed", "useless", "do nothing",
            "bai yi komai ba", "empty promises",
            "nothing to show"
        ]):
            attack_type = "performance_attack"

        return {
            "is_attack": True,
            "threat_level": threat,
            "attack_type": attack_type,
            "keywords_found": all_hits,
            "keyword_count": hit_count,
            "language": (
                "hausa" if hausa_hits
                else "english"
            ),
            "requires_immediate_response": (
                threat in ["CRITICAL", "HIGH"]
            ),
        }

    async def run_full_scan(self) -> List[Dict]:
        all_items = []

        try:
            mentions = (
                await self.get_recent_mentions()
            )
            for m in mentions:
                content = (
                    m.get("title", "") + " "
                    + m.get("description", "")
                )
                analysis = self.analyze_for_attacks(
                    content
                )
                if analysis["is_attack"]:
                    all_items.append({
                        "id": m.get("id", ""),
                        "platform": m.get(
                            "source_type", "social"
                        ),
                        "source_name": m.get(
                            "source", "Unknown"
                        ),
                        "content": content[:500],
                        "url": m.get(
                            "original_url", ""
                        ),
                        "author": m.get(
                            "author_name", "Unknown"
                        ),
                        "published": m.get(
                            "date", ""
                        ),
                        "analysis": analysis,
                        "status": "pending_review",
                        "scanned_at": (
                            datetime.now().isoformat()
                        ),
                    })
        except Exception as e:
            print(f"Mention scan error: {e}")

        try:
            news_items = (
                await self.scrape_google_news()
            )
            for item in news_items:
                content = (
                    item.get("title", "") + " "
                    + item.get("content", "")
                )
                analysis = self.analyze_for_attacks(
                    content, "news"
                )
                if analysis["is_attack"]:
                    all_items.append({
                        "id": f"news_{len(all_items)}",
                        "platform": "news",
                        "source_name": item.get(
                            "source", "News"
                        ),
                        "content": content[:500],
                        "url": item.get("url", ""),
                        "author": "News Article",
                        "published": item.get(
                            "published", ""
                        ),
                        "analysis": analysis,
                        "status": "pending_review",
                        "scanned_at": (
                            datetime.now().isoformat()
                        ),
                    })
        except Exception as e:
            print(f"News scan error: {e}")

        priority = {
            "CRITICAL": 0,
            "HIGH": 1,
            "MEDIUM": 2,
        }
        all_items.sort(
            key=lambda x: priority.get(
                x["analysis"]["threat_level"], 3
            )
        )
        return all_items


scraper_service = ScraperService()