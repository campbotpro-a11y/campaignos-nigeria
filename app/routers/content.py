from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ContentRequest,
    ContentResponse,
)
from app.services.ai_service import ai_service
from app.services.airtable_service import (
    airtable_service,
)

router = APIRouter(
    prefix="/content", tags=["Content Engine"]
)


@router.post(
    "/generate", response_model=ContentResponse
)
async def generate_content(
    request: ContentRequest,
):
    try:
        body_text = await ai_service.generate_content(
            content_type=request.content_type,
            platform=request.platform,
            topic=request.topic or "",
            tone=request.tone or "professional",
            language=request.language or "hausa",
        )
        record = airtable_service.save_content({
            "title": (
                f"{request.content_type}"
                f" — {request.platform}"
            ),
            "content_type": request.content_type,
            "platform": request.platform,
            "body_text": body_text,
            "language": request.language or "Hausa",
        })
        return ContentResponse(
            content_type=request.content_type,
            platform=request.platform,
            body_text=body_text,
            language=request.language or "hausa",
            airtable_record_id=record.get("id"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@router.post("/rebuttal")
async def generate_rebuttal(attack_text: str):
    try:
        rebuttal = await ai_service.generate_content(
            content_type="rebuttal",
            platform="all",
            topic=attack_text,
            language="hausa",
        )
        record = airtable_service.save_content({
            "title": "Rapid Response Rebuttal",
            "content_type": "Rebuttal",
            "platform": "All Platforms",
            "body_text": rebuttal,
            "language": "English + Hausa",
        })
        return {
            "rebuttal": rebuttal,
            "saved_to_airtable": record.get("id"),
            "status": "PENDING HUMAN REVIEW",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@router.get("/pending")
async def get_pending_content():
    try:
        records = (
            airtable_service.get_pending_content()
        )
        return {
            "count": len(records),
            "items": [
                {
                    "id": r["id"],
                    "title": r["fields"].get(
                        "Content Title"
                    ),
                    "type": r["fields"].get(
                        "Content Type"
                    ),
                    "language": r["fields"].get(
                        "Language"
                    ),
                    "preview": (
                        r["fields"].get(
                            "Body Text", ""
                        )[:120] + "..."
                    ),
                }
                for r in records
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )