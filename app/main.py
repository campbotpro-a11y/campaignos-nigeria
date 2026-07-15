from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    whatsapp,
    content,
    supporters,
    analytics,
    nedc,
    sms,
    warroom,
)

app = FastAPI(
    title="CampaignOS Nigeria",
    description=(
        "AI Campaign Operating System — "
        "Dr. Ismaila Dahuwa Kaila, "
        "Bauchi North, PRP 2027"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp.router)
app.include_router(content.router)
app.include_router(supporters.router)
app.include_router(analytics.router)
app.include_router(nedc.router)
app.include_router(sms.router)
app.include_router(warroom.router)


@app.get("/")
async def root():
    return {
        "system": "CampaignOS Nigeria",
        "client": "Dr. Ismaila Dahuwa Kaila",
        "district": "Bauchi North",
        "party": "PRP",
        "election": "2027",
        "status": "operational",
        "modules": [
            "whatsapp_bot",
            "content_engine",
            "supporter_crm",
            "bulk_sms",
            "war_room",
            "facebook_posting",
            "analytics",
            "nedc_intelligence",
        ],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}