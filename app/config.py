import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── AI ─────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv(
        "OPENAI_API_KEY", ""
    )
    ANTHROPIC_API_KEY: str = os.getenv(
        "ANTHROPIC_API_KEY", ""
    )

    # ── WhatsApp ───────────────────────────────
    DIALOG360_API_KEY: str = os.getenv(
        "DIALOG360_API_KEY", ""
    )
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv(
        "WHATSAPP_PHONE_NUMBER_ID", ""
    )
    VERIFY_TOKEN: str = os.getenv(
        "VERIFY_TOKEN", "campaignos_dahuwa_2027"
    )

    # ── Airtable ───────────────────────────────
    AIRTABLE_API_KEY: str = os.getenv(
        "AIRTABLE_API_KEY", ""
    )
    AIRTABLE_BASE_ID: str = os.getenv(
        "AIRTABLE_BASE_ID", ""
    )

    # ── Facebook ───────────────────────────────
    FACEBOOK_PAGE_ID: str = os.getenv(
        "FACEBOOK_PAGE_ID", ""
    )
    FACEBOOK_PAGE_TOKEN: str = os.getenv(
        "FACEBOOK_PAGE_TOKEN", ""
    )
    FACEBOOK_APP_ID: str = os.getenv(
        "FACEBOOK_APP_ID", ""
    )
    FACEBOOK_APP_SECRET: str = os.getenv(
        "FACEBOOK_APP_SECRET", ""
    )

    # ── SMS — Termii ───────────────────────────
    TERMII_API_KEY: str = os.getenv(
        "TERMII_API_KEY", ""
    )
    TERMII_SENDER_ID: str = os.getenv(
        "TERMII_SENDER_ID", "DAHUWA"
    )

    # ── SMS — Africa's Talking ─────────────────
    AT_USERNAME: str = os.getenv(
        "AT_USERNAME", ""
    )
    AT_API_KEY: str = os.getenv(
        "AT_API_KEY", ""
    )
    AT_SENDER_ID: str = os.getenv(
        "AT_SENDER_ID", "DAHUWA2027"
    )

    # ── SMS — BulkSMS Nigeria ──────────────────
    BULKSMS_NG_USERNAME: str = os.getenv(
        "BULKSMS_NG_USERNAME", ""
    )
    BULKSMS_NG_API_KEY: str = os.getenv(
        "BULKSMS_NG_API_KEY", ""
    )
    BULKSMS_NG_SENDER: str = os.getenv(
        "BULKSMS_NG_SENDER", "DAHUWA2027"
    )

    # ── Social Monitoring ──────────────────────
    MENTION_API_KEY: str = os.getenv(
        "MENTION_API_KEY", ""
    )
    MENTION_ACCOUNT_ID: str = os.getenv(
        "MENTION_ACCOUNT_ID", ""
    )

    # ── Campaign ───────────────────────────────
    CAMPAIGN_MANAGER_PHONE: str = os.getenv(
        "CAMPAIGN_MANAGER_PHONE", ""
    )

    # ── App ────────────────────────────────────
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", ""
    )
    APP_ENV: str = os.getenv(
        "APP_ENV", "development"
    )


settings = Settings()