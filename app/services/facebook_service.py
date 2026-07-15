import httpx
from app.config import settings
from typing import Optional

GRAPH_BASE = "https://graph.facebook.com/v19.0"


class FacebookService:

    def __init__(self):
        self.page_id = settings.FACEBOOK_PAGE_ID
        self.token = settings.FACEBOOK_PAGE_TOKEN

    async def post_to_page(
        self,
        message: str,
        link: Optional[str] = None,
    ) -> dict:
        payload = {
            "message": message,
            "access_token": self.token,
        }
        if link:
            payload["link"] = link

        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            r = await client.post(
                f"{GRAPH_BASE}/{self.page_id}/feed",
                data=payload,
            )
        result = r.json()

        if "id" in result:
            post_id = result["id"]
            return {
                "success": True,
                "post_id": post_id,
                "post_url": (
                    f"https://facebook.com/"
                    f"{post_id.replace('_', '/posts/')}"
                ),
                "message_preview": (
                    message[:100] + "..."
                ),
            }
        return {
            "success": False,
            "error": result.get(
                "error", {}
            ).get("message", "Unknown error"),
            "raw": result,
        }

    async def post_with_image(
        self,
        message: str,
        image_url: str,
    ) -> dict:
        payload = {
            "message": message,
            "url": image_url,
            "access_token": self.token,
        }
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            r = await client.post(
                f"{GRAPH_BASE}/{self.page_id}/photos",
                data=payload,
            )
        return r.json()

    async def get_recent_posts(
        self, limit: int = 10
    ) -> list:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            r = await client.get(
                f"{GRAPH_BASE}/{self.page_id}/posts",
                params={
                    "fields": (
                        "id,message,created_time,"
                        "likes.summary(true),"
                        "comments.summary(true),"
                        "shares"
                    ),
                    "limit": limit,
                    "access_token": self.token,
                },
            )
        return r.json().get("data", [])

    async def get_page_insights(self) -> dict:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            r = await client.get(
                f"{GRAPH_BASE}/{self.page_id}"
                f"/insights",
                params={
                    "metric": (
                        "page_fans,"
                        "page_views_total,"
                        "page_post_engagements"
                    ),
                    "period": "week",
                    "access_token": self.token,
                },
            )
        data = r.json()
        insights = {}
        for item in data.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [])
            if values:
                insights[name] = values[-1].get(
                    "value", 0
                )
        return insights

    async def reply_to_comment(
        self,
        comment_id: str,
        reply_text: str,
    ) -> dict:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            r = await client.post(
                f"{GRAPH_BASE}/{comment_id}/comments",
                data={
                    "message": reply_text,
                    "access_token": self.token,
                },
            )
        return r.json()

    async def delete_post(
        self, post_id: str
    ) -> dict:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            r = await client.delete(
                f"{GRAPH_BASE}/{post_id}",
                params={
                    "access_token": self.token
                },
            )
        return r.json()


facebook_service = FacebookService()