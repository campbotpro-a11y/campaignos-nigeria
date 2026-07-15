import json
from app.config import settings
from app.services.ai_service import ai_service
from app.services.facebook_service import (
    facebook_service,
)
from app.services.whatsapp_service import (
    whatsapp_service,
)
from app.services.airtable_service import (
    airtable_service,
)
from typing import Dict, Optional

RESPONSE_PROMPTS = {
    "corruption_allegation": """
        {PROFILE}
        A corruption allegation has been made:
        "{content}"
        Generate a response:
        ENGLISH STATEMENT: [150 words, firm, dignified,
        references verifiable record, invites investigation]
        HAUSA VERSION: [80 words]
        TALKING POINTS:
        • [point 1]
        • [point 2]
        • [point 3]
    """,
    "integrity_attack": """
        {PROFILE}
        An integrity/honesty attack:
        "{content}"
        Generate a response:
        ENGLISH STATEMENT: [150 words, factual rebuttal,
        points to transparent Senate record]
        HAUSA VERSION: [80 words]
        TALKING POINTS:
        • [point 1]
        • [point 2]
        • [point 3]
    """,
    "party_loyalty_attack": """
        {PROFILE}
        A party loyalty attack:
        "{content}"
        Generate a response that owns party changes
        confidently and connects PRP to Aminu Kano:
        ENGLISH STATEMENT: [150 words]
        HAUSA VERSION: [80 words]
        TALKING POINTS:
        • [point 1]
        • [point 2]
        • [point 3]
    """,
    "performance_attack": """
        {PROFILE}
        A performance attack:
        "{content}"
        Generate a response listing specific
        achievements and NEDC projects:
        ENGLISH STATEMENT: [150 words]
        HAUSA VERSION: [80 words]
        TALKING POINTS:
        • [point 1]
        • [point 2]
        • [point 3]
    """,
    "general_attack": """
        {PROFILE}
        An attack has been made:
        "{content}"
        Generate a calm dignified response:
        ENGLISH STATEMENT: [150 words]
        HAUSA VERSION: [80 words]
        TALKING POINTS:
        • [point 1]
        • [point 2]
        • [point 3]
    """,
}

CANDIDATE_PROFILE = """
Dr. Ismaila Dahuwa Kaila — PRP Senator,
Bauchi North. Former Health Commissioner.
Medical doctor. 2023 victory: 1,797 vote margin.
Key achievements: ₦2.1B NEDC projects for
Bauchi North including Azare-Kafin Madaki road,
Katagum hospital equipment, 12 school renovations.
"""


class WarRoomService:

    async def process_attack(
        self, attack_data: Dict
    ) -> Dict:
        content = attack_data.get("content", "")
        analysis = attack_data.get("analysis", {})
        attack_type = analysis.get(
            "attack_type", "general_attack"
        )
        threat_level = analysis.get(
            "threat_level", "MEDIUM"
        )
        platform = attack_data.get(
            "platform", "unknown"
        )
        source = attack_data.get(
            "source_name", "Unknown"
        )
        url = attack_data.get("url", "")

        prompt_template = RESPONSE_PROMPTS.get(
            attack_type,
            RESPONSE_PROMPTS["general_attack"],
        )
        prompt = prompt_template.format(
            PROFILE=CANDIDATE_PROFILE,
            content=content[:300],
        )

        ai_response = await ai_service.generate_content(
            content_type="rebuttal",
            platform="facebook",
            topic=prompt,
            language="english",
        )

        parsed = self._parse_response(ai_response)

        try:
            record = airtable_service.save_content({
                "title": (
                    f"War Room — {attack_type}"
                    f" — {platform}"
                ),
                "content_type": "Rebuttal",
                "platform": "Facebook",
                "body_text": ai_response,
                "language": "English + Hausa",
            })
            record_id = record.get("id", "")
        except Exception:
            record_id = ""

        approval_id = (
            f"WR_{platform[:3].upper()}_"
            f"{len(content) % 9999:04d}"
        )

        package = {
            "approval_id": approval_id,
            "attack_data": attack_data,
            "analysis": analysis,
            "ai_response": {
                "english_statement": parsed.get(
                    "english", ai_response[:400]
                ),
                "hausa_version": parsed.get(
                    "hausa", ""
                ),
                "talking_points": parsed.get(
                    "points", []
                ),
                "facebook_post": parsed.get(
                    "english", ai_response[:400]
                ),
            },
            "airtable_record_id": record_id,
            "status": "PENDING_APPROVAL",
        }

        await self._send_whatsapp_alert(
            package, threat_level, platform,
            source, url, approval_id,
        )

        return package

    def _parse_response(
        self, response: str
    ) -> Dict:
        result = {
            "english": "",
            "hausa": "",
            "points": [],
        }
        lines = response.split("\n")
        current = None
        current_text = []

        for line in lines:
            lu = line.upper().strip()
            if "ENGLISH STATEMENT" in lu:
                if current and current_text:
                    result[current] = (
                        "\n".join(
                            current_text
                        ).strip()
                    )
                current = "english"
                current_text = []
            elif "HAUSA VERSION" in lu:
                if current and current_text:
                    result[current] = (
                        "\n".join(
                            current_text
                        ).strip()
                    )
                current = "hausa"
                current_text = []
            elif "TALKING POINTS" in lu:
                if current and current_text:
                    result[current] = (
                        "\n".join(
                            current_text
                        ).strip()
                    )
                current = "points"
                current_text = []
            else:
                if current == "points":
                    pt = line.strip().lstrip(
                        "•-123. "
                    )
                    if pt:
                        result["points"].append(pt)
                elif current in ["english", "hausa"]:
                    current_text.append(line)

        if current in ["english", "hausa"]:
            if current_text:
                result[current] = "\n".join(
                    current_text
                ).strip()

        return result

    async def _send_whatsapp_alert(
        self,
        package: Dict,
        threat_level: str,
        platform: str,
        source: str,
        url: str,
        approval_id: str,
    ) -> None:
        manager_phone = (
            settings.CAMPAIGN_MANAGER_PHONE
        )
        if not manager_phone:
            return

        emoji = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️",
            "MEDIUM": "📋",
        }.get(threat_level, "📋")

        ai_resp = package.get("ai_response", {})
        english = ai_resp.get(
            "english_statement", ""
        )[:250]
        hausa = ai_resp.get(
            "hausa_version", ""
        )[:150]
        points = ai_resp.get("talking_points", [])
        attack_preview = package.get(
            "attack_data", {}
        ).get("content", "")[:150]

        alert = (
            f"{emoji} *WAR ROOM ALERT*\n"
            f"Threat: *{threat_level}*\n\n"
            f"Platform: *{platform.upper()}*\n"
            f"Source: {source}\n"
            f"URL: {url or 'N/A'}\n\n"
            f"*ATTACK:*\n\"{attack_preview}...\"\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"*AI DRAFT RESPONSE:*\n\n"
            f"🇬🇧 {english}...\n\n"
            f"🇳🇬 {hausa}\n\n"
            f"📌 POINTS:\n"
            + "\n".join(
                f"• {p}" for p in points[:3]
            )
            + f"\n\n━━━━━━━━━━━━━━━━\n"
            f"ID: *{approval_id}*\n\n"
            f"Reply:\n"
            f"*APPROVE {approval_id}*\n"
            f"*REJECT {approval_id}*\n\n"
            f"⏰ Respond within 2 hours."
        )

        try:
            await whatsapp_service.send_message(
                manager_phone, alert
            )
        except Exception as e:
            print(f"Alert send error: {e}")

    async def execute_approval(
        self,
        approval_id: str,
        approved_text: Optional[str] = None,
        pending_approvals: dict = {},
    ) -> Dict:
        package = pending_approvals.get(approval_id)
        if not package:
            return {
                "error": (
                    f"ID {approval_id} not found"
                    f" or expired"
                )
            }

        post_text = (
            approved_text
            or package["ai_response"]["facebook_post"]
        )

        result = await facebook_service.post_to_page(
            post_text
        )

        if result.get("success"):
            hausa_text = package[
                "ai_response"
            ].get("hausa_version", "")
            if hausa_text:
                try:
                    from app.services.sms_service \
                        import sms_service
                    all_s = (
                        airtable_service
                        .get_all_supporters()
                    )
                    phones = [
                        r["fields"].get(
                            "WhatsApp Number"
                        ) or r["fields"].get(
                            "Phone Number"
                        )
                        for r in all_s[:200]
                        if r["fields"].get(
                            "WhatsApp Number"
                        ) or r["fields"].get(
                            "Phone Number"
                        )
                    ]
                    if phones:
                        await sms_service.smart_send(
                            phones,
                            hausa_text[:160],
                            "termii",
                        )
                except Exception as e:
                    print(f"Broadcast error: {e}")

            return {
                "success": True,
                "approval_id": approval_id,
                "facebook_post": result,
                "whatsapp_broadcast": (
                    "sent to top 200 supporters"
                ),
                "posted_text": (
                    post_text[:200] + "..."
                ),
            }

        return {
            "success": False,
            "approval_id": approval_id,
            "error": result.get("error"),
        }


warroom_service = WarRoomService()