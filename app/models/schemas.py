from pydantic import BaseModel
from typing import Optional, List


class SupporterCreate(BaseModel):
    full_name: str
    phone: str
    whatsapp: Optional[str] = None
    state: str = "Bauchi"
    lga: str
    ward: Optional[str] = None
    polling_unit: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    how_they_heard: Optional[str] = None


class ContentRequest(BaseModel):
    content_type: str
    platform: str
    topic: Optional[str] = None
    tone: Optional[str] = "professional"
    language: Optional[str] = "hausa"


class ContentResponse(BaseModel):
    content_type: str
    platform: str
    body_text: str
    language: str
    airtable_record_id: Optional[str] = None


class RallyEvent(BaseModel):
    event_name: str
    date_time: str
    location: str
    lga: str
    expected_attendance: Optional[int] = None


class BroadcastRequest(BaseModel):
    lga: Optional[str] = None
    message: str
    target: Optional[str] = "all"


class SMSRequest(BaseModel):
    message: str
    provider: Optional[str] = "termii"
    sender_id: Optional[str] = None


class WardSMSRequest(BaseModel):
    ward: str
    lga: str
    message: str
    provider: Optional[str] = "termii"


class AIMessageRequest(BaseModel):
    target: str
    topic: str
    lga: Optional[str] = None
    ward: Optional[str] = None
    language: Optional[str] = "hausa"
    provider: Optional[str] = "termii"