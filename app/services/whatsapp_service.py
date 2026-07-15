import httpx
from app.config import settings


class WhatsAppService:
    def __init__(self):
        self.base_url = "https://waba.360dialog.io/v1"
        self.headers = {
            "D360-API-KEY": settings.DIALOG360_API_KEY,
            "Content-Type": "application/json",
        }

    def _clean_number(self, number: str) -> str:
        n = (
            number.strip()
            .replace("+", "")
            .replace(" ", "")
            .replace("-", "")
        )
        if n.startswith("0"):
            n = "234" + n[1:]
        if not n.startswith("234"):
            n = "234" + n
        return n

    async def send_message(
        self, to: str, message: str
    ) -> dict:
        to_clean = self._clean_number(to)
        payload = {
            "messaging_product": "whatsapp",
            "to": to_clean,
            "type": "text",
            "text": {"body": message},
        }
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            r = await client.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=self.headers,
            )
        return r.json()

    async def send_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list,
    ) -> dict:
        to_clean = self._clean_number(to)
        button_list = [
            {
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}",
                    "title": str(btn)[:20],
                },
            }
            for i, btn in enumerate(buttons[:3])
        ]
        payload = {
            "messaging_product": "whatsapp",
            "to": to_clean,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": button_list},
            },
        }
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            r = await client.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=self.headers,
            )
        return r.json()

    async def send_broadcast(
        self, phone_numbers: list, message: str
    ) -> dict:
        results = []
        for number in phone_numbers:
            try:
                result = await self.send_message(
                    number, message
                )
                results.append({
                    "number": number,
                    "status": "sent",
                    "result": result,
                })
            except Exception as e:
                results.append({
                    "number": number,
                    "status": "failed",
                    "error": str(e),
                })
        sent = sum(
            1 for r in results
            if r["status"] == "sent"
        )
        return {
            "total": len(phone_numbers),
            "sent": sent,
            "failed": len(phone_numbers) - sent,
            "results": results,
        }


whatsapp_service = WhatsAppService()