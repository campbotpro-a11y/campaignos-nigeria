from pyairtable import Api
from app.config import settings
from typing import Optional, List, Dict, Any


class AirtableService:
    def __init__(self):
        self.api = Api(settings.AIRTABLE_API_KEY)
        self.base_id = settings.AIRTABLE_BASE_ID

    def get_table(self, table_name: str):
        return self.api.table(self.base_id, table_name)

    # ── SUPPORTERS ─────────────────────────────────
    def add_supporter(
        self, data: Dict[str, Any]
    ) -> Dict:
        table = self.get_table("Supporters")
        return table.create({
            "Full Name": data.get("full_name", ""),
            "Phone Number": data.get("phone", ""),
            "WhatsApp Number": data.get(
                "whatsapp", data.get("phone", "")
            ),
            "State": "Bauchi",
            "LGA": data.get("lga", ""),
            "Ward": data.get("ward", ""),
            "Polling Unit": data.get(
                "polling_unit", ""
            ),
            "Age": data.get("age"),
            "Gender": data.get("gender", ""),
            "Occupation": data.get("occupation", ""),
            "How They Heard": data.get(
                "how_they_heard", "WhatsApp"
            ),
            "Support Level": "Leaning",
            "Volunteer?": False,
        })

    def get_all_supporters(self) -> List[Dict]:
        return self.get_table("Supporters").all()

    def get_supporters_by_lga(
        self, lga: str
    ) -> List[Dict]:
        return self.get_table("Supporters").all(
            formula=f"{{LGA}}='{lga}'"
        )

    def get_supporters_by_ward(
        self, ward: str, lga: str
    ) -> List[Dict]:
        return self.get_table("Supporters").all(
            formula=f"AND({{Ward}}='{ward}',"
                    f"{{LGA}}='{lga}')"
        )

    def get_supporters_by_polling_unit(
        self, polling_unit: str, ward: str, lga: str
    ) -> List[Dict]:
        return self.get_table("Supporters").all(
            formula=f"AND({{Polling Unit}}="
                    f"'{polling_unit}',"
                    f"{{Ward}}='{ward}',"
                    f"{{LGA}}='{lga}')"
        )

    def count_supporters_by_lga(
        self,
    ) -> Dict[str, int]:
        all_s = self.get_all_supporters()
        counts = {}
        for r in all_s:
            lga = r["fields"].get("LGA", "Unknown")
            counts[lga] = counts.get(lga, 0) + 1
        return counts

    # ── VOLUNTEERS ─────────────────────────────────
    def add_volunteer(
        self, data: Dict[str, Any]
    ) -> Dict:
        table = self.get_table("Volunteers")
        record = table.create({
            "Volunteer Name": data.get("name", ""),
            "Phone": data.get("phone", ""),
            "LGA": data.get("lga", ""),
            "Ward": data.get("ward", ""),
            "Task Status": "Not Started",
        })
        # Mark as volunteer in Supporters table too
        supporters = self.get_table("Supporters")
        existing = supporters.all(
            formula=f"{{Phone Number}}="
                    f"'{data.get('phone')}'"
        )
        if existing:
            supporters.update(
                existing[0]["id"],
                {"Volunteer?": True}
            )
        return record

    def get_all_volunteers(self) -> List[Dict]:
        return self.get_table("Volunteers").all()

    # ── CONTENT ────────────────────────────────────
    def save_content(
        self, data: Dict[str, Any]
    ) -> Dict:
        table = self.get_table("Content Library")
        return table.create({
            "Content Title": data.get("title", ""),
            "Content Type": data.get(
                "content_type", ""
            ),
            "Platform": [data.get(
                "platform", "WhatsApp"
            )],
            "Body Text": data.get("body_text", ""),
            "Language": data.get("language", "Hausa"),
            "Status": "AI Draft",
        })

    def get_pending_content(self) -> List[Dict]:
        return self.get_table(
            "Content Library"
        ).all(formula="{Status}='AI Draft'")

    # ── RALLY EVENTS ───────────────────────────────
    def get_upcoming_rallies(self) -> List[Dict]:
        return self.get_table("Rally Events").all(
            formula="OR({Status}='Confirmed',"
                    "{Status}='Planning')"
        )

    def create_rally(
        self, data: Dict[str, Any]
    ) -> Dict:
        return self.get_table("Rally Events").create({
            "Event Name": data.get(
                "event_name", ""
            ),
            "Date & Time": data.get(
                "date_time", ""
            ),
            "Location/Venue": data.get(
                "location", ""
            ),
            "LGA": data.get("lga", ""),
            "Expected Attendance": data.get(
                "expected_attendance", 0
            ),
            "Confirmed RSVPs": 0,
            "Status": "Planning",
        })

    def log_sms(
        self, data: Dict[str, Any]
    ) -> Dict:
        return self.get_table("SMS Log").create({
            "Campaign Title": data.get("title", ""),
            "Target Type": data.get(
                "target_type", ""
            ),
            "Target LGA": data.get("lga", ""),
            "Target Ward": data.get("ward", ""),
            "Message Text": data.get("message", ""),
            "Provider Used": data.get(
                "provider", ""
            ),
            "Numbers Sent": data.get("sent", 0),
            "Numbers Failed": data.get("failed", 0),
            "Cost Naira": data.get("cost", 0),
            "Status": "Sent",
        })


airtable_service = AirtableService()