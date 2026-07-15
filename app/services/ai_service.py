import anthropic
import openai
import json
from app.config import settings

CANDIDATE_PROFILE = """
Candidate: Dr. Ismaila Dahuwa Kaila
Office: Nigerian Senate — Bauchi North
Status: Incumbent Senator seeking re-election 2027
Party: Peoples Redemption Party (PRP)
Party Journey: PDP (2023 win) → APC (Oct 2025)
               → PRP (May 2026, denied APC ticket)
Key Ally: Senator Shehu Buba (PRP governorship)

District LGAs: Katagum (HQ: Azare), Misau, Dambam,
               Zaki, Gamawa, Jama'are, Itas-Gadau,
               Shira/Giade

2023 Victory Margin: 1,797 votes over APC

Core Narrative:
"I refused to be controlled by party godfathers.
They denied my ticket. I now stand with the party
of Aminu Kano — the party of the talakawa."

Background: Medical doctor, former Commissioner
for Health, Bauchi State

Tone: Man of the people. Wronged but not bitter.
Confident. Islamic values. Hausa-dominant.
"""

claude_client = anthropic.Anthropic(
    api_key=settings.ANTHROPIC_API_KEY
)
openai_client = openai.OpenAI(
    api_key=settings.OPENAI_API_KEY
)


class AIService:

    async def generate_content(
        self,
        content_type: str,
        platform: str,
        topic: str = "",
        tone: str = "professional",
        language: str = "hausa",
    ) -> str:

        lang_instruction = (
            "Respond in natural conversational Hausa. "
            "Use Islamic greetings (Assalamu Alaikum, "
            "Alhamdulillah) where appropriate."
            if language == "hausa"
            else "Respond in clear Nigerian English."
            if language == "english"
            else "Mix Hausa and English naturally."
        )

        prompts = {
            "morning_post": f"""
                {CANDIDATE_PROFILE}
                {lang_instruction}
                Generate a warm {platform} morning post.
                Topic: {topic or 'general campaign'}
                - Islamic greeting opening
                - Everyday Bauchi North life reference
                - ONE campaign message woven in
                - Engagement question at end
                - Max 120 words. No excessive hashtags.
            """,
            "prp_narrative": f"""
                {CANDIDATE_PROFILE}
                {lang_instruction}
                Generate a post explaining the PRP
                journey honestly — turning it to strength.
                - Own party changes confidently
                - Frame as: refused godfather control
                - Connect to Aminu Kano talakawa legacy
                - Direct appeal to Bauchi North voters
                - Max 150 words. Passionate but dignified.
            """,
            "rebuttal": f"""
                {CANDIDATE_PROFILE}
                {lang_instruction}
                Draft a rapid response rebuttal.
                Attack to respond to: {topic}
                Format exactly:
                ENGLISH STATEMENT: [150 words, dignified]
                HAUSA VERSION: [80 words]
                TALKING POINTS:
                • [point 1]
                • [point 2]
                • [point 3]
                Never attack individuals by name.
                Stay factual and forward-looking.
            """,
            "whatsapp_broadcast": f"""
                {CANDIDATE_PROFILE}
                {lang_instruction}
                Write WhatsApp broadcast message.
                Topic: {topic or 'campaign update'}
                - Conversational, warm Nigerian tone
                - Clear call-to-action
                - End: share with 5 supporters
                - Max 100 words
            """,
            "rally_announcement": f"""
                {CANDIDATE_PROFILE}
                {lang_instruction}
                Write rally announcement broadcast.
                Event details: {topic}
                - Exciting, urgent energy
                - Clear date, time, location
                - Call to bring family and friends
                - Max 100 words
            """,
            "joint_prp": f"""
                {CANDIDATE_PROFILE}
                {lang_instruction}
                Generate joint PRP campaign content
                featuring Dr. Dahuwa (Senate) and
                Senator Shehu Buba (Governor).
                Show PRP as serious force in Bauchi.
                Encourage voting PRP for both seats.
                Reference Aminu Kano legacy.
                Max 130 words.
            """,
            "press_statement": f"""
                {CANDIDATE_PROFILE}
                Write formal press statement in English.
                Topic: {topic or 'campaign announcement'}
                Format: Headline + Date + 3 paragraphs
                + Quote from Dr. Dahuwa
                Professional, newsworthy. Max 300 words.
            """,
            "youth_engagement": f"""
                {CANDIDATE_PROFILE}
                {lang_instruction}
                Generate content targeting youth
                aged 18-30 in Bauchi North.
                Topic: {topic}
                - Acknowledge their skepticism directly
                - Speak to jobs, education, NPOWER
                - ONE concrete verifiable promise
                - Youthful but respectful tone
                - Mix English and Hausa naturally
                - Max 120 words
            """,
            "nedc_content": f"""
                {CANDIDATE_PROFILE}
                {lang_instruction}
                Generate NEDC accountability content.
                Topic: {topic}
                - Reference NEDC mandate for North East
                - Show Dr. Dahuwa's advocacy record
                - Specific projects facilitated
                - Promise for second term oversight
                - Max 150 words
            """,
        }

        prompt = prompts.get(
            content_type,
            f"{CANDIDATE_PROFILE}\n{lang_instruction}\n"
            f"Generate {content_type} content. "
            f"Topic: {topic}. Max 150 words.",
        )

        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return message.content[0].text

    async def generate_bot_response(
        self,
        user_message: str,
        conversation_history: list = [],
    ) -> str:
        system_prompt = f"""
        You are the official 24/7 WhatsApp campaign
        assistant for Dr. Ismaila Dahuwa Kaila.

        {CANDIDATE_PROFILE}

        RULES:
        1. Answer only about Dr. Dahuwa and campaign
        2. Respond in same language user writes in
           (Hausa → Hausa, English → English)
        3. For party change questions: own it
           confidently, never apologize
        4. For attacks: stay calm and factual
        5. End with volunteer invite OR rally
           reminder OR share request
        6. Keep under 160 words for WhatsApp
        7. Use Islamic greetings for Hausa messages
        8. Never promise specific money amounts
           unless in approved manifesto
        """

        messages = [
            *conversation_history,
            {"role": "user", "content": user_message},
        ]

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                *messages,
            ],
            max_tokens=300,
        )
        return response.choices[0].message.content

    async def analyze_sentiment(
        self, text: str
    ) -> dict:
        prompt = f"""
        Analyze this content about a Nigerian
        political campaign:
        "{text}"

        Return ONLY valid JSON, nothing else:
        {{
          "sentiment": "positive" or "negative"
                       or "neutral",
          "score": 0.0 to 1.0,
          "key_concerns": ["concern1", "concern2"],
          "requires_response": true or false,
          "urgency": "low" or "medium" or "high"
        }}
        """
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        try:
            return json.loads(
                message.content[0].text
            )
        except Exception:
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "key_concerns": [],
                "requires_response": False,
                "urgency": "low",
            }


ai_service = AIService()