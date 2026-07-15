from fastapi import APIRouter, Request, HTTPException
from app.config import settings
from app.services.ai_service import ai_service
from app.services.whatsapp_service import (
    whatsapp_service,
)
from app.services.airtable_service import (
    airtable_service,
)

router = APIRouter(
    prefix="/whatsapp", tags=["WhatsApp"]
)

sessions = {}

MAIN_MENU = (
    "Assalamu Alaikum warahmatullahi! 🤝\n\n"
    "*Dr. Ismaila Dahuwa Kaila*\n"
    "Sanatan Bauchi North — PRP 2027 🟢\n\n"
    "Zan iya taimaka maka.\n\n"
    "Zaɓi lamba:\n"
    "1️⃣ Ayyukan Sanata\n"
    "2️⃣ Dalilin PRP\n"
    "3️⃣ Zama Mai Sa Kai\n"
    "4️⃣ Taruka Mai Zuwa\n"
    "5️⃣ Tambaya\n"
    "6️⃣ English Menu"
)

ENGLISH_MENU = (
    "Welcome! 🤝\n\n"
    "*Dr. Ismaila Dahuwa Kaila*\n"
    "Senator, Bauchi North — PRP 2027 🟢\n\n"
    "How can I help?\n\n"
    "1️⃣ Senator's Achievements\n"
    "2️⃣ Why PRP?\n"
    "3️⃣ Become a Volunteer\n"
    "4️⃣ Upcoming Rallies\n"
    "5️⃣ Ask a Question\n"
    "6️⃣ Hausa Menu"
)

WHY_PRP = (
    "*Dalilin da ya sa na zaɓi PRP:*\n\n"
    "APC sun ƙi bani tikitin komawa — "
    "ba saboda na gaza ba.\n"
    "Sai don na ƙi biya wa godfathers biyayya.\n\n"
    "Na zaɓi PRP — jam'iyyar Aminu Kano.\n"
    "Jam'iyyar talakawa. Jam'iyyar gaskiya.\n\n"
    "Amincina ga ku ya fi kowane jam'iyya. 🇳🇬\n\n"
    "Reply *MENU* don komawa."
)

LGA_MENU = (
    "Wane LGA kake so ka ji ayyukan?\n\n"
    "1. Katagum/Azare\n"
    "2. Misau\n"
    "3. Dambam\n"
    "4. Zaki\n"
    "5. Gamawa\n"
    "6. Jama'are\n"
    "7. Itas-Gadau\n"
    "8. Shira/Giade"
)

LGA_ACHIEVEMENTS = {
    "katagum": (
        "📍 *Katagum LGA — Azare*\n\n"
        "Ayyukan Dr. Dahuwa:\n"
        "✅ Titin Azare–Kafin Madaki (₦480M NEDC)\n"
        "✅ Asibitin Azare — kayan aiki sabbi\n"
        "✅ Makarantu 12 — littattafai da kujeru\n"
        "✅ Rijiyoyin ruwa 8 a ƙauyuka 4\n\n"
        "Azare ita ce zuciyar Bauchi North! 🏙️\n\n"
        "Reply *MENU* don komawa."
    ),
    "misau": (
        "📍 *Misau LGA*\n\n"
        "Ayyukan Dr. Dahuwa:\n"
        "✅ UBEC kuɗi ga makarantu 3\n"
        "✅ NYSC posting — graduates 47\n"
        "✅ Hanyar Misau–Gwaram — ci gaba\n\n"
        "Misau — ƙarfi da al'adu! 💪\n\n"
        "Reply *MENU* don komawa."
    ),
    "dambam": (
        "📍 *Dambam LGA*\n\n"
        "Ayyukan Dr. Dahuwa:\n"
        "✅ Hanyar kasuwanci ta Gombe\n"
        "✅ Tallafi ga manoman auduga\n"
        "✅ Ruwa mai tsafta ga ƙauyuka 3\n\n"
        "Dambam — ƙofa ta Gombe. 🌾\n\n"
        "Reply *MENU* don komawa."
    ),
    "zaki": (
        "📍 *Zaki LGA*\n\n"
        "Ayyukan Dr. Dahuwa:\n"
        "✅ Tallafi ga al'ummomin kan iyaka ta Yobe\n"
        "✅ Goyon bayan kiwo da noma\n"
        "✅ Makaranta mai sabbin kujeru\n\n"
        "Zaki — ƙarfi da juriya. 🦁\n\n"
        "Reply *MENU* don komawa."
    ),
    "gamawa": (
        "📍 *Gamawa LGA*\n\n"
        "Ayyukan Dr. Dahuwa:\n"
        "✅ Aikin raya al'umma — Kafin Madaki\n"
        "✅ Hanyar zuwa kasuwa ta gwamnatin tarayya\n"
        "✅ Tallafi ga matasa\n\n"
        "Gamawa — ƙasar shugabanni. 👑\n\n"
        "Reply *MENU* don komawa."
    ),
    "jamare": (
        "📍 *Jama'are LGA*\n\n"
        "Ayyukan Dr. Dahuwa:\n"
        "✅ Aikin noma a bakin kogin Jama'are\n"
        "✅ Kasuwanci ta iyaka ta Jigawa\n"
        "✅ Asibitin PHC an gyara\n\n"
        "Jama'are — ruwa da albarka. 💧\n\n"
        "Reply *MENU* don komawa."
    ),
    "itas": (
        "📍 *Itas-Gadau LGA*\n\n"
        "Ayyukan Dr. Dahuwa:\n"
        "✅ Hanyoyin karkara an gyara\n"
        "✅ Tallafi ga manoma\n"
        "✅ Makaranta sabuwa\n\n"
        "Itas-Gadau — ba a mance da ku ba. ❤️\n\n"
        "Reply *MENU* don komawa."
    ),
    "shira": (
        "📍 *Shira/Giade LGA*\n\n"
        "Ayyukan Dr. Dahuwa:\n"
        "✅ Kasuwanci ta iyaka ta Kano\n"
        "✅ Goyon bayan noma da kiwo\n"
        "✅ Ruwa mai tsafta ga gidaje\n\n"
        "Shira da Giade — ginshiƙin Bauchi North. 🌟\n\n"
        "Reply *MENU* don komawa."
    ),
}

PARTY_CHANGE_RESPONSE = (
    "Tambaya mai kyau — zan amsa da gaskiya.\n\n"
    "Na fara da PDP, na koma APC, yanzu ina PRP.\n\n"
    "Dalilin: Kowace canjin jam'iyya na yi, "
    "na nemi wuri da zan iya yin aiki "
    "ba tare da godfathers suna sarrafa ni ba.\n\n"
    "APC sun ƙi ba ni tikiti — ba domin "
    "na gaza ba. Sai don na ƙi biya biyayya.\n\n"
    "PRP ita ce jam'iyyar Aminu Kano. "
    "Jam'iyyar talakawa. Ina gida.\n\n"
    "Amincina ga ku ya fi kowane jam'iyya. 🇳🇬\n\n"
    "Ku yi hukunci da ayyukana.\n\n"
    "Reply *MENU* don ƙarin bayani."
)

VOLUNTEER_DONE = (
    "✅ *An yi rijista da nasara!*\n\n"
    "Barka, {name}! 🎉\n\n"
    "Ka zama wani ɓangare na tawagar "
    "Dr. Dahuwa a Bauchi North.\n\n"
    "Wani daga tawagar zai tuntuɓe ka "
    "cikin awanni 24.\n\n"
    "Tare da kai, za mu ci nasara! 💪🇳🇬\n\n"
    "Reply *MENU* don ƙarin bayani."
)


@router.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token")
        == settings.VERIFY_TOKEN
    ):
        return int(
            params.get("hub.challenge", 0)
        )
    raise HTTPException(
        status_code=403,
        detail="Verification failed",
    )


@router.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    try:
        entry = body["entry"][0]
        value = entry["changes"][0]["value"]
        if "messages" not in value:
            return {"status": "ok"}
        message = value["messages"][0]
        from_number = message["from"]
        msg_type = message.get("type", "text")

        if msg_type == "text":
            user_text = (
                message["text"]["body"].strip()
            )
        elif msg_type == "interactive":
            user_text = message["interactive"][
                "button_reply"
            ]["title"]
        else:
            await whatsapp_service.send_message(
                from_number,
                "Da fatan za a aika saƙon rubutu.\n"
                "Reply MENU don farawa.",
            )
            return {"status": "ok"}

        await handle_message(
            from_number, user_text
        )
        return {"status": "ok"}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error"}


async def handle_message(
    phone: str, text: str
):
    t = text.lower().strip()

    # ── War room approval commands ──────────────
    if t.startswith("approve "):
        parts = text.strip().split(" ", 1)
        if len(parts) == 2:
            approval_id = parts[1].upper()
            try:
                from app.routers.warroom import (
                    pending_approvals,
                    approve_response,
                )
                result = await approve_response(
                    approval_id
                )
                if result.get("success"):
                    await whatsapp_service.send_message(
                        phone,
                        f"✅ Posted to Facebook!\n"
                        f"URL: {result.get('facebook_post', {}).get('post_url', 'N/A')}",
                    )
                else:
                    await whatsapp_service.send_message(
                        phone,
                        f"❌ Error: {result.get('error', 'Unknown')}",
                    )
            except Exception as e:
                await whatsapp_service.send_message(
                    phone, f"Error: {str(e)}"
                )
            return

    if t.startswith("reject "):
        parts = text.strip().split(" ", 1)
        if len(parts) == 2:
            approval_id = parts[1].upper()
            try:
                from app.routers.warroom import (
                    pending_approvals,
                )
                if approval_id in pending_approvals:
                    del pending_approvals[
                        approval_id
                    ]
                await whatsapp_service.send_message(
                    phone,
                    "🚫 Response rejected. "
                    "No post made to Facebook.",
                )
            except Exception as e:
                print(f"Reject error: {e}")
            return

    # ── Menu resets ─────────────────────────────
    if t in [
        "menu", "start", "farawa", "hello",
        "hi", "salam", "help", "taimako", "0",
    ]:
        await whatsapp_service.send_buttons(
            phone,
            MAIN_MENU,
            ["1 Ayyuka", "2 Dalilin PRP", "3 Volunteer"],
        )
        return

    if t in ["6", "english", "english menu"]:
        await whatsapp_service.send_buttons(
            phone,
            ENGLISH_MENU,
            ["1 Achievements", "2 Why PRP", "3 Volunteer"],
        )
        return

    # ── Main menu selections ─────────────────────
    if t in ["1", "ayyukan sanata", "achievements",
             "1 ayyuka"]:
        await whatsapp_service.send_message(
            phone, LGA_MENU
        )
        return

    if t in ["2", "dalilin prp", "why prp",
             "2 dalilin prp"]:
        await whatsapp_service.send_message(
            phone, WHY_PRP
        )
        return

    if t in ["3", "zama mai sa kai", "volunteer",
             "3 volunteer"]:
        await start_volunteer_flow(phone)
        return

    if t in ["4", "taruka", "rallies",
             "upcoming rallies"]:
        await send_rallies(phone)
        return

    if t in ["5", "tambaya", "ask", "question"]:
        sessions[phone] = {"step": "open_question"}
        await whatsapp_service.send_message(
            phone,
            "Ka/ki rubuta tambayarka yanzu. ✍️\n"
            "(Type your question now.)\n\n"
            "Zan amsa da gaskiya. 💚",
        )
        return

    # ── LGA selections ───────────────────────────
    lga_map = {
        "1": "katagum",
        "katagum": "katagum",
        "azare": "katagum",
        "2": "misau",
        "misau": "misau",
        "3": "dambam",
        "dambam": "dambam",
        "4": "zaki",
        "zaki": "zaki",
        "5": "gamawa",
        "gamawa": "gamawa",
        "6": "jamare",
        "jama'are": "jamare",
        "jamare": "jamare",
        "7": "itas",
        "itas-gadau": "itas",
        "itas gadau": "itas",
        "8": "shira",
        "shira": "shira",
        "giade": "shira",
        "shira/giade": "shira",
    }
    if t in lga_map:
        msg = LGA_ACHIEVEMENTS.get(lga_map[t], "")
        if msg:
            await whatsapp_service.send_message(
                phone, msg
            )
            return

    # ── Party change keywords ────────────────────
    party_keywords = [
        "party", "pdp", "apc", "prp", "canja",
        "why change", "me ya sa", "traitor",
        "karya", "munafiki", "jumper",
        "political prostitute", "3 times",
    ]
    if any(k in t for k in party_keywords):
        await whatsapp_service.send_message(
            phone, PARTY_CHANGE_RESPONSE
        )
        return

    # ── Active session (registration/question) ───
    if phone in sessions:
        await process_session(phone, text)
        return

    # ── Default: AI handles it ───────────────────
    response = await ai_service.generate_bot_response(
        text, []
    )
    await whatsapp_service.send_message(
        phone, response
    )


async def start_volunteer_flow(phone: str):
    sessions[phone] = {"step": "name"}
    await whatsapp_service.send_message(
        phone,
        "Nagode sosai! 🙌\n\n"
        "Muna buƙatar mutane masu gaskiya "
        "kamar kai/ki.\n\n"
        "Da fatan za a faɗa "
        "*sunan ka/ki cikakke*:",
    )


async def process_session(
    phone: str, text: str
):
    session = sessions.get(phone, {})
    step = session.get("step")

    if step == "name":
        session["name"] = text
        session["step"] = "lga"
        sessions[phone] = session
        await whatsapp_service.send_message(
            phone,
            f"Nagode, *{text}*! 🇳🇬\n\n"
            "Kana/kina wane LGA?\n\n"
            "1. Katagum  2. Misau  3. Dambam\n"
            "4. Zaki     5. Gamawa 6. Jama'are\n"
            "7. Itas-Gadau  8. Shira/Giade",
        )

    elif step == "lga":
        session["lga"] = text
        session["step"] = "ward"
        sessions[phone] = session
        await whatsapp_service.send_message(
            phone,
            f"*{text}* — nagode! 📍\n\n"
            "Wane ward/ƙauye kake/kike?",
        )

    elif step == "ward":
        session["ward"] = text
        try:
            airtable_service.add_volunteer({
                "name": session.get("name", ""),
                "phone": phone,
                "lga": session.get("lga", ""),
                "ward": text,
            })
        except Exception as e:
            print(f"Volunteer save error: {e}")

        name = session.get("name", "")
        del sessions[phone]

        await whatsapp_service.send_message(
            phone,
            VOLUNTEER_DONE.format(name=name),
        )

    elif step == "open_question":
        del sessions[phone]
        response = (
            await ai_service.generate_bot_response(
                text, []
            )
        )
        await whatsapp_service.send_message(
            phone, response
        )


async def send_rallies(phone: str):
    try:
        rallies = (
            airtable_service.get_upcoming_rallies()
        )
        if not rallies:
            await whatsapp_service.send_message(
                phone,
                "📍 Babu taruka da aka tabbatar.\n\n"
                "Mu bi mu a WhatsApp don sanarwa.\n"
                "Reply *MENU* don komawa.",
            )
            return

        msg = "📍 *TARUKAN DR. DAHUWA MAI ZUWA*\n\n"
        for r in rallies[:3]:
            f = r["fields"]
            msg += (
                f"🗓️ *{f.get('Event Name', 'TBA')}*\n"
                f"📅 {f.get('Date & Time', 'TBA')}\n"
                f"📌 {f.get('Location/Venue', 'TBA')}"
                f", {f.get('LGA', '')}\n\n"
            )
        msg += (
            "Reply *RSVP* don tabbatar zuwa.\n"
            "(Reply RSVP to confirm attendance.)"
        )
        await whatsapp_service.send_message(
            phone, msg
        )
    except Exception as e:
        print(f"Rally error: {e}")
        await whatsapp_service.send_message(
            phone,
            "Ana loda bayanan taruka...\n"
            "Da fatan za a sake gwadawa daga baya.",
        )