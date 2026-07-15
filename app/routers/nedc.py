from fastapi import APIRouter, HTTPException
from app.services.ai_service import ai_service

router = APIRouter(
    prefix="/nedc", tags=["NEDC Intelligence"]
)

NEDC_CONTEXT = """
North East Development Commission (NEDC):
- Established 2017 for post-insurgency rebuild
- Covers Borno, Yobe, Adamawa, Gombe,
  Bauchi, Taraba
- Annual allocation: ₦100B+
- Focus: Roads, schools, hospitals, IDPs

Dr. Dahuwa as PRP senator = independent voice
demanding NEDC accountability without ruling
party constraints. This is a KEY advantage.

Bauchi North projects facilitated:
- Azare–Kafin Madaki road (₦480M)
- Katagum General Hospital equipment
- 12 school renovations across 4 LGAs
"""


@router.get("/talking-points")
async def get_talking_points():
    try:
        result = await ai_service.generate_content(
            content_type="nedc_content",
            platform="all",
            topic=(
                f"5 powerful NEDC campaign talking "
                f"points for senator. Include: bold "
                f"claim, evidence, promise, Hausa "
                f"version. Context: {NEDC_CONTEXT}"
            ),
            language="english",
        )
        return {"talking_points": result}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )


@router.post("/rebuttal")
async def nedc_rebuttal(attack: str):
    try:
        result = await ai_service.generate_content(
            content_type="rebuttal",
            platform="all",
            topic=(
                f"NEDC attack to rebut: {attack}. "
                f"Context: {NEDC_CONTEXT}"
            ),
            language="hausa",
        )
        return {
            "attack": attack,
            "response": result,
            "status": "PENDING HUMAN REVIEW",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e)
        )