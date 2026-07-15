from fastapi import APIRouter, HTTPException
from app.models.schemas import SupporterCreate
from app.services.airtable_service import (
    airtable_service,
)
from app.services.whatsapp_service import (
    whatsapp_service,
)

router = APIRouter(
    prefix="/supporters", tags=["Supporter CRM"]
)

WELCOME_MSG = (
    "Assalamu Alaikum, *{name}*! 🎉\n\n"
    "An yi rijistarka cikin nasara a "
    "tawagar Dr. Ismaila Dahuwa Kaila.\n\n"
    "Muna godiya da goyan bayanka!\n"
    "Tare, za mu canza Bauchi North. 🇳🇬\n\n"
    "Aika MENU don duba zaɓuɓɓuka."
)


@router.post("/register")
async def register_supporter(
    supporter: SupporterCreate,
):
    try:
        record = airtable_service.add_supporter(
            supporter.dict()
        )
        try:
            await whatsapp_service.send_message(
                supporter.whatsapp or supporter.phone,
                WELCOME_MSG.format(
                    name=supporter.full_name
                ),
            )
        except Exception:
            pass
        return {
            "success": True,
            "message": (
                f"Welcome, {supporter.full_name}!"
            ),
            "record_id": record.get("id"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@router.get("/stats")
async def get_stats():
    try:
        all_s = airtable_service.get_all_supporters()
        total = len(all_s)
        volunteers = sum(
            1 for r in all_s
            if r["fields"].get("Volunteer?")
        )
        lga_counts = (
            airtable_service.count_supporters_by_lga()
        )
        top_lgas = sorted(
            lga_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return {
            "total_supporters": total,
            "total_volunteers": volunteers,
            "lga_breakdown": [
                {"lga": l, "count": c}
                for l, c in top_lgas
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@router.post("/broadcast")
async def broadcast_to_lga(
    lga: str, message: str
):
    try:
        supporters = (
            airtable_service.get_supporters_by_lga(
                lga
            )
        )
        phones = [
            r["fields"].get("WhatsApp Number")
            or r["fields"].get("Phone Number")
            for r in supporters
            if r["fields"].get("WhatsApp Number")
            or r["fields"].get("Phone Number")
        ]
        if not phones:
            return {
                "error": f"No supporters in {lga}"
            }
        result = (
            await whatsapp_service.send_broadcast(
                phones, message
            )
        )
        return {
            "lga": lga,
            "targeted": len(phones),
            "result": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@router.get("/polling-unit-coverage")
async def polling_unit_coverage():
    try:
        all_s = airtable_service.get_all_supporters()
        unit_coverage = {}
        for r in all_s:
            f = r["fields"]
            unit = f.get("Polling Unit", "Unassigned")
            lga = f.get("LGA", "Unknown")
            ward = f.get("Ward", "Unknown")
            key = f"{lga}|{ward}|{unit}"
            if key not in unit_coverage:
                unit_coverage[key] = {
                    "lga": lga,
                    "ward": ward,
                    "polling_unit": unit,
                    "supporter_count": 0,
                    "volunteer_count": 0,
                }
            unit_coverage[key][
                "supporter_count"
            ] += 1
            if f.get("Volunteer?"):
                unit_coverage[key][
                    "volunteer_count"
                ] += 1

        units = list(unit_coverage.values())
        critical = [
            u for u in units
            if u["supporter_count"] <= 5
        ]
        low = [
            u for u in units
            if 6 <= u["supporter_count"] <= 20
        ]
        moderate = [
            u for u in units
            if 21 <= u["supporter_count"] <= 50
        ]
        strong = [
            u for u in units
            if u["supporter_count"] > 50
        ]

        return {
            "summary": {
                "total_units": len(units),
                "critical": len(critical),
                "low": len(low),
                "moderate": len(moderate),
                "strong": len(strong),
            },
            "priority_action": critical[:20],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )