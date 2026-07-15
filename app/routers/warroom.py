from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    BackgroundTasks,
)
from app.services.scraper_service import (
    scraper_service,
)
from app.services.warroom_service import (
    warroom_service,
)
from app.services.facebook_service import (
    facebook_service,
)
from app.config import settings
from typing import Optional
import asyncio

router = APIRouter(
    prefix="/warroom", tags=["War Room"]
)

pending_approvals: dict = {}


@router.get("/scan")
async def run_scan(
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(
        _run_scan_background
    )
    return {
        "status": "scan_started",
        "message": (
            "Scanning all platforms. "
            "Results sent via WhatsApp."
        ),
    }


@router.get("/scan/now")
async def run_scan_now():
    attacks = await scraper_service.run_full_scan()

    if not attacks:
        return {
            "attacks_found": 0,
            "message": "No attacks detected.",
            "platforms_checked": [
                "Facebook", "Twitter/X",
                "TikTok", "Blogs", "News",
            ],
        }

    critical = [
        a for a in attacks
        if a["analysis"]["threat_level"]
        in ["CRITICAL", "HIGH"]
    ]

    processed = []
    for attack in critical[:3]:
        package = (
            await warroom_service.process_attack(
                attack
            )
        )
        approval_id = package.get(
            "approval_id", ""
        )
        if approval_id:
            pending_approvals[
                approval_id
            ] = package
        processed.append({
            "approval_id": approval_id,
            "platform": attack.get("platform"),
            "threat_level": (
                attack["analysis"]["threat_level"]
            ),
            "attack_type": (
                attack["analysis"]["attack_type"]
            ),
            "content_preview": (
                attack.get("content", "")[:100]
                + "..."
            ),
            "status": "approval_sent_via_whatsapp",
        })

    return {
        "attacks_found": len(attacks),
        "critical_processed": len(processed),
        "processed_attacks": processed,
    }


@router.post("/webhook")
async def mention_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    body = await request.json()
    try:
        mention = body.get("mention", body)
        title = mention.get("title", "")
        description = mention.get(
            "description", ""
        )
        content = f"{title} {description}"
        source = mention.get("source", {})

        analysis = (
            scraper_service.analyze_for_attacks(
                content
            )
        )
        if not analysis["is_attack"]:
            return {
                "status": "ok",
                "action": "not an attack",
            }

        attack_data = {
            "id": mention.get("id", ""),
            "platform": source.get(
                "media_type", "social"
            ),
            "source_name": source.get(
                "title", "Unknown"
            ),
            "content": content[:500],
            "url": mention.get(
                "original_url", ""
            ),
            "author": mention.get(
                "author", {}
            ).get("name", "Unknown"),
            "published": mention.get(
                "published_at", ""
            ),
            "analysis": analysis,
            "status": "pending_review",
        }

        background_tasks.add_task(
            _process_single_attack, attack_data
        )

        return {
            "status": "ok",
            "action": "processing",
            "threat_level": (
                analysis["threat_level"]
            ),
        }
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error"}


@router.post("/approve/{approval_id}")
async def approve_response(
    approval_id: str,
    edited_text: Optional[str] = None,
):
    if approval_id not in pending_approvals:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Approval ID {approval_id} "
                f"not found or expired."
            ),
        )

    result = await warroom_service.execute_approval(
        approval_id=approval_id,
        approved_text=edited_text,
        pending_approvals=pending_approvals,
    )

    if result.get("success"):
        del pending_approvals[approval_id]

    return result


@router.post("/reject/{approval_id}")
async def reject_response(
    approval_id: str,
    reason: Optional[str] = None,
):
    if approval_id in pending_approvals:
        del pending_approvals[approval_id]
    return {
        "status": "rejected",
        "approval_id": approval_id,
        "reason": reason or "Rejected by team",
        "action": "No post made to Facebook",
    }


@router.get("/pending")
async def get_pending():
    pending = []
    for aid, package in pending_approvals.items():
        attack = package.get("attack_data", {})
        analysis = package.get("analysis", {})
        ai_resp = package.get("ai_response", {})
        pending.append({
            "approval_id": aid,
            "platform": attack.get("platform"),
            "threat_level": analysis.get(
                "threat_level"
            ),
            "attack_type": analysis.get(
                "attack_type"
            ),
            "attack_preview": (
                attack.get("content", "")[:100]
                + "..."
            ),
            "response_preview": (
                ai_resp.get(
                    "english_statement", ""
                )[:150] + "..."
            ),
            "source": attack.get("source_name"),
            "url": attack.get("url"),
        })
    return {
        "pending_count": len(pending),
        "pending_approvals": sorted(
            pending,
            key=lambda x: {
                "CRITICAL": 0,
                "HIGH": 1,
                "MEDIUM": 2,
            }.get(
                x.get("threat_level", ""), 3
            ),
        ),
    }


@router.post("/facebook/post")
async def post_to_facebook(
    message: str,
    link: Optional[str] = None,
):
    result = await facebook_service.post_to_page(
        message, link
    )
    return result


@router.get("/facebook/posts")
async def get_facebook_posts():
    posts = await facebook_service.get_recent_posts(
        10
    )
    return {
        "page_id": settings.FACEBOOK_PAGE_ID,
        "recent_posts": [
            {
                "id": p.get("id"),
                "message": p.get(
                    "message", ""
                )[:200],
                "created": p.get("created_time"),
                "likes": p.get(
                    "likes", {}
                ).get("summary", {}).get(
                    "total_count", 0
                ),
                "comments": p.get(
                    "comments", {}
                ).get("summary", {}).get(
                    "total_count", 0
                ),
                "shares": p.get(
                    "shares", {}
                ).get("count", 0),
            }
            for p in posts
        ],
    }


@router.get("/facebook/insights")
async def get_insights():
    insights = (
        await facebook_service.get_page_insights()
    )
    return {
        "page_id": settings.FACEBOOK_PAGE_ID,
        "insights": insights,
    }


async def _run_scan_background():
    try:
        attacks = (
            await scraper_service.run_full_scan()
        )
        for attack in attacks[:5]:
            if attack["analysis"][
                "threat_level"
            ] in ["CRITICAL", "HIGH"]:
                package = (
                    await warroom_service
                    .process_attack(attack)
                )
                aid = package.get(
                    "approval_id", ""
                )
                if aid:
                    pending_approvals[aid] = package
                await asyncio.sleep(2)
    except Exception as e:
        print(f"Scan background error: {e}")


async def _process_single_attack(
    attack_data: dict,
):
    try:
        package = (
            await warroom_service.process_attack(
                attack_data
            )
        )
        aid = package.get("approval_id", "")
        if aid:
            pending_approvals[aid] = package
    except Exception as e:
        print(f"Attack processing error: {e}")