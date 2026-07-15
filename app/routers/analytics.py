from fastapi import APIRouter, HTTPException
from app.services.airtable_service import (
    airtable_service,
)
from app.services.ai_service import ai_service

router = APIRouter(
    prefix="/analytics", tags=["Analytics"]
)

BAUCHI_NORTH_LGAS = [
    "Katagum", "Misau", "Dambam", "Zaki",
    "Gamawa", "Jama'are", "Itas-Gadau",
    "Shira/Giade",
]


@router.get("/dashboard")
async def get_dashboard():
    try:
        supporters = (
            airtable_service.get_all_supporters()
        )
        volunteers = (
            airtable_service.get_all_volunteers()
        )
        rallies = (
            airtable_service.get_upcoming_rallies()
        )
        content = (
            airtable_service.get_pending_content()
        )
        lga_counts = (
            airtable_service.count_supporters_by_lga()
        )

        weak_lgas = [
            lga for lga in BAUCHI_NORTH_LGAS
            if lga_counts.get(lga, 0) == 0
        ]

        return {
            "summary": {
                "total_supporters": len(supporters),
                "total_volunteers": len(volunteers),
                "content_pending_review": len(
                    content
                ),
                "upcoming_rallies": len(rallies),
            },
            "margin_alert": {
                "2023_winning_margin": 1797,
                "warning": (
                    "THIN MARGIN — every ward counts"
                ),
                "lgas_with_zero_coverage": weak_lgas,
            },
            "lga_coverage": [
                {
                    "lga": lga,
                    "supporters": lga_counts.get(
                        lga, 0
                    ),
                    "status": (
                        "STRONG"
                        if lga_counts.get(lga, 0)
                        >= 100
                        else "MODERATE"
                        if lga_counts.get(lga, 0)
                        >= 30
                        else "WEAK"
                        if lga_counts.get(lga, 0) > 0
                        else "ZERO — URGENT"
                    ),
                }
                for lga in BAUCHI_NORTH_LGAS
            ],
            "upcoming_rallies": [
                {
                    "name": r["fields"].get(
                        "Event Name"
                    ),
                    "date": r["fields"].get(
                        "Date & Time"
                    ),
                    "lga": r["fields"].get("LGA"),
                    "rsvps": r["fields"].get(
                        "Confirmed RSVPs", 0
                    ),
                }
                for r in rallies[:5]
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@router.post("/sentiment")
async def analyze_sentiment(text: str):
    try:
        return await ai_service.analyze_sentiment(
            text
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@router.get("/margin-protection")
async def margin_protection():
    try:
        all_s = airtable_service.get_all_supporters()
        total = len(all_s)
        volunteers = sum(
            1 for r in all_s
            if r["fields"].get("Volunteer?")
        )
        safety_target = 5000
        coverage_pct = min(
            round(
                (total / safety_target) * 100, 1
            ),
            100,
        )
        lga_counts = (
            airtable_service.count_supporters_by_lga()
        )
        weakest = sorted(
            lga_counts.items(),
            key=lambda x: x[1],
        )[:3]

        return {
            "margin_context": {
                "2023_winning_margin": 1797,
                "votes_to_flip": 900,
                "warning": "THIN MARGIN",
            },
            "coverage_status": {
                "supporters_mapped": total,
                "safety_target": safety_target,
                "coverage_percent": coverage_pct,
                "status": (
                    "SAFE"
                    if coverage_pct >= 80
                    else "AT RISK"
                    if coverage_pct >= 50
                    else "CRITICAL"
                ),
            },
            "volunteers_active": volunteers,
            "weakest_lgas": [
                {
                    "lga": lga,
                    "supporters": count,
                    "action": "MOBILIZE IMMEDIATELY",
                }
                for lga, count in weakest
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )