import httpx
from app.config import settings
from typing import Optional


class SMSService:

    def _format_number(self, number: str) -> str:
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

    def _format_numbers_list(
        self, numbers: list
    ) -> list:
        return [
            self._format_number(n)
            for n in numbers
            if n and len(str(n)) >= 10
        ]

    async def send_via_termii(
        self,
        phone_numbers: list,
        message: str,
        sender_id: Optional[str] = None,
    ) -> dict:
        formatted = self._format_numbers_list(
            phone_numbers
        )
        if not formatted:
            return {"error": "No valid numbers"}

        sender = sender_id or settings.TERMII_SENDER_ID
        results = []
        chunks = [
            formatted[i: i + 100]
            for i in range(0, len(formatted), 100)
        ]

        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            for chunk in chunks:
                payload = {
                    "to": chunk,
                    "from": sender,
                    "sms": message[:160],
                    "type": "plain",
                    "api_key": settings.TERMII_API_KEY,
                    "channel": "generic",
                }
                try:
                    r = await client.post(
                        "https://api.ng.termii.com"
                        "/api/sms/send/bulk",
                        json=payload,
                    )
                    results.append(r.json())
                except Exception as e:
                    results.append(
                        {"error": str(e)}
                    )

        return {
            "provider": "Termii",
            "total": len(formatted),
            "results": results,
            "estimated_cost_naira": (
                len(formatted) * 5
            ),
        }

    async def send_via_africas_talking(
        self,
        phone_numbers: list,
        message: str,
        sender_id: Optional[str] = None,
    ) -> dict:
        formatted = self._format_numbers_list(
            phone_numbers
        )
        if not formatted:
            return {"error": "No valid numbers"}

        sender = sender_id or settings.AT_SENDER_ID
        recipients = ",".join(
            [f"+{n}" for n in formatted]
        )

        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            try:
                r = await client.post(
                    "https://api.africastalking.com"
                    "/version1/messaging",
                    data={
                        "username": (
                            settings.AT_USERNAME
                        ),
                        "to": recipients,
                        "message": message[:160],
                        "from": sender,
                    },
                    headers={
                        "apiKey": settings.AT_API_KEY,
                        "Accept": "application/json",
                    },
                )
                return {
                    "provider": "Africa's Talking",
                    "total": len(formatted),
                    "raw": r.json(),
                    "estimated_cost_naira": (
                        len(formatted) * 10
                    ),
                }
            except Exception as e:
                return {
                    "provider": "Africa's Talking",
                    "error": str(e),
                }

    async def send_via_bulksms_nigeria(
        self,
        phone_numbers: list,
        message: str,
        sender_id: Optional[str] = None,
    ) -> dict:
        formatted = self._format_numbers_list(
            phone_numbers
        )
        if not formatted:
            return {"error": "No valid numbers"}

        sender = (
            sender_id or settings.BULKSMS_NG_SENDER
        )
        recipients = ",".join(formatted)

        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            try:
                r = await client.get(
                    "https://www.bulksmsnigeria.com"
                    "/api/v1/sms/create",
                    params={
                        "api_token": (
                            settings.BULKSMS_NG_API_KEY
                        ),
                        "from": sender,
                        "to": recipients,
                        "body": message[:160],
                        "dnd": 2,
                    },
                )
                return {
                    "provider": "BulkSMS Nigeria",
                    "total": len(formatted),
                    "raw": r.json(),
                    "estimated_cost_naira": (
                        len(formatted) * 4
                    ),
                }
            except Exception as e:
                return {
                    "provider": "BulkSMS Nigeria",
                    "error": str(e),
                }

    async def smart_send(
        self,
        phone_numbers: list,
        message: str,
        preferred_provider: str = "termii",
        sender_id: Optional[str] = None,
    ) -> dict:
        providers = {
            "termii": self.send_via_termii,
            "africas_talking": (
                self.send_via_africas_talking
            ),
            "bulksms_nigeria": (
                self.send_via_bulksms_nigeria
            ),
        }
        order = [preferred_provider] + [
            p for p in providers
            if p != preferred_provider
        ]
        last_error = None
        for provider_name in order:
            fn = providers.get(provider_name)
            if not fn:
                continue
            try:
                result = await fn(
                    phone_numbers,
                    message,
                    sender_id,
                )
                if "error" not in result:
                    result["provider_used"] = (
                        provider_name
                    )
                    result["fallback_used"] = (
                        provider_name
                        != preferred_provider
                    )
                    return result
                last_error = result.get("error")
            except Exception as e:
                last_error = str(e)
                continue

        return {
            "error": "All providers failed",
            "last_error": last_error,
            "providers_tried": order,
        }

    async def send_to_ward(
        self,
        ward: str,
        lga: str,
        message: str,
        provider: str = "termii",
    ) -> dict:
        from app.services.airtable_service import (
            airtable_service,
        )
        records = (
            airtable_service.get_supporters_by_ward(
                ward, lga
            )
        )
        phones = [
            r["fields"].get("Phone Number")
            for r in records
            if r["fields"].get("Phone Number")
        ]
        if not phones:
            return {
                "ward": ward,
                "lga": lga,
                "error": "No supporters in this ward",
            }
        result = await self.smart_send(
            phones, message, provider
        )
        result["ward"] = ward
        result["lga"] = lga
        result["supporters_targeted"] = len(phones)
        return result

    async def send_to_polling_unit(
        self,
        polling_unit: str,
        ward: str,
        lga: str,
        message: str,
        provider: str = "termii",
    ) -> dict:
        from app.services.airtable_service import (
            airtable_service,
        )
        records = (
            airtable_service
            .get_supporters_by_polling_unit(
                polling_unit, ward, lga
            )
        )
        phones = [
            r["fields"].get("Phone Number")
            for r in records
            if r["fields"].get("Phone Number")
        ]
        if not phones:
            return {
                "polling_unit": polling_unit,
                "error": "No supporters at this unit",
            }
        result = await self.smart_send(
            phones, message, provider
        )
        result["polling_unit"] = polling_unit
        result["ward"] = ward
        result["lga"] = lga
        result["supporters_targeted"] = len(phones)
        return result


sms_service = SMSService()