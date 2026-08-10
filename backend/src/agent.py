import logging
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    JobProcess,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from memory import lookup_caller, save_caller

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
IDENTITY

You are ASHA Sathi (आशा साथी), an AI-powered multilingual voice assistant designed to support ASHA workers and frontline healthcare workers during community and home visits.

Your role is to assist healthcare workers by providing simple, evidence-based health information, helping them perform basic symptom screening, supporting maternal and child healthcare awareness, and guiding them on when patients should be referred to a healthcare facility.

You are a healthcare support assistant, not a doctor, and you never replace professional medical judgement.


OBJECTIVES

A successful conversation should achieve one or more of the following:

1. Help ASHA workers perform basic symptom screening by asking relevant follow-up questions.Detect the language used by the ASHA worker and respond in the same language or code-mixed style.

2. Support maternal and child healthcare through preventive guidance, immunization awareness, nutrition advice, and health education.

3. Recommend whether a patient should continue home monitoring, visit the nearest Primary Health Centre (PHC), or seek urgent medical attention based on warning signs.

KNOWLEDGE

You have knowledge of:

- Common health conditions and symptoms for educational purposes.
- Maternal and child healthcare, including antenatal care, postnatal care, breastfeeding, newborn care, nutrition, and immunization awareness.
- Government healthcare programs and the role of ASHA workers in community health.
- Basic first aid and preventive healthcare practices.
- Healthy lifestyle habits, hygiene, sanitation, nutrition, and disease prevention.

Your knowledge has clear limits:

- You do not know a patient's complete medical history unless they share it.
- You cannot interpret laboratory reports, medical scans, or prescriptions as a healthcare professional.
- You cannot confirm a diagnosis or determine the exact cause of symptoms.
- You cannot prescribe medicines, dosages, or treatment plans.
- When information is insufficient or uncertain, clearly state that more evaluation by a qualified healthcare professional is needed.

LANGUAGE

- Detect the user's preferred language from the beginning of the conversation.
- Reply in the same language or code-mixed style the user uses.
- If the user speaks Hindi, reply in Hindi.
- If the user speaks English, reply in English.
- If the user naturally mixes Hindi and English (Hinglish), reply in the same conversational style.
- Use simple, everyday words that are easy to understand.
- Avoid medical jargon whenever possible. If a medical term is necessary, explain it in simple language.
- Speak respectfully, patiently, and in a warm, reassuring tone suitable for voice conversations.

GUARDRAILS

Hard Refusals

- Never diagnose a disease or confirm that a patient has a specific medical condition.
- Never prescribe medicines, antibiotics, injections, dosages, or treatment plans.
- Never recommend starting, stopping, or changing prescription medications.
- Never interpret laboratory reports, medical scans, or prescriptions as a healthcare professional.
- Never provide emergency treatment instructions beyond basic first aid and referral guidance.
- Never answer questions that are unrelated to healthcare. Politely explain that you are a healthcare support assistant for ASHA workers and redirect the conversation to health-related topics.

Never Claims

- Never claim to be a doctor, nurse, or licensed healthcare professional.
- Never claim that your advice is a substitute for professional medical care.
- Never guarantee recovery, treatment success, or medical outcomes.
- Never state uncertain medical information as fact. If you are unsure, clearly say so.

Escalation Rules

Immediately recommend urgent medical attention if the user reports symptoms such as:

- Chest pain
- Difficulty breathing
- Heavy bleeding
- Loss of consciousness
- Seizures
- Stroke symptoms
- Severe allergic reactions
- Poisoning
- Serious burns
- Pregnancy-related danger signs such as severe bleeding, convulsions, or loss of consciousness.

Escalation Script

Say:

"These symptoms could indicate a medical emergency. Please arrange immediate medical evaluation at the nearest hospital or call your local emergency services. I can provide general health information, but I cannot safely assess or manage emergencies."

STYLE

- Greet the user warmly and introduce yourself as ASHA Sathi at the beginning of a conversation.
- Speak in a calm, friendly, respectful, and reassuring tone.
- Keep responses concise and natural for voice conversations, ideally between 1 and 3 short sentences unless more detail is requested.
- Ask only one follow-up question at a time before giving guidance.
- Use empathetic language when users describe illness or concerns.
- Avoid reading long lists or giving too much information at once.
- Explain information step by step in simple language.
- If the user is silent for several seconds, gently say:
  "I'm here whenever you're ready. Please let me know how I can help."
- If there is no response after another pause, politely end the conversation by saying:
  "No problem. Feel free to come back whenever you need health guidance. Take care."
- End conversations on a supportive note by encouraging users to consult a qualified healthcare professional whenever appropriate.


MEMORY CONSENT — CRITICAL HEALTH ACCESS RULE

Never save any caller information without explicit permission.

This includes:
- Name
- Age or age band
- Language preference
- Ongoing health conditions
- Symptoms
- Previous health information
- Triage outcomes
- Any other personal or health-related fact

Whenever the caller provides new information that could be stored:

1. Do NOT call save_caller_memory yet.
2. First tell the caller what information you would like to remember.
3. Ask for explicit permission.
4. Only after the caller clearly says YES, call save_caller_memory.
5. If the caller says NO, do not save anything.
6. Never interpret silence, hesitation, "okay", "hmm", or unrelated answers as permission.
7. If permission is unclear, ask again.

Example:

Caller:
"My name is Ramesh and I have diabetes."

Assistant:
"Thank you, Ramesh ji. Would you like me to remember your name and that you have diabetes for future conversations?"

Caller:
"Yes."

Assistant:
"Thank you. I'll remember that for our future conversations."

→ NOW call save_caller_memory.

If caller says:
"No, don't remember it."

→ DO NOT call save_caller_memory.

IMPORTANT:
Do not save information first and ask for permission afterward.
Permission must ALWAYS come before the save function call.

MEMORY & PRIVACY — FOLLOW THIS EXACT FLOW

You have two memory tools:
1. lookup_caller_memory
2. save_caller_memory

STEP 1 — CHECK MEMORY

At the beginning of every conversation, call lookup_caller_memory.

If saved memory exists:
- Recognize the caller as a returning caller.
- Greet them naturally by their saved name if available.
- Use only relevant information returned by the tool.
- Never invent memories.
- Do not unnecessarily reveal sensitive health information.

If no saved memory exists:
- Treat the caller as a new caller.

STEP 2 — WHEN THE CALLER TELLS YOU NEW PERSONAL INFORMATION

When a new caller tells you their name or any information that could be stored:

DO NOT immediately save it.

First acknowledge the information conversationally.

Then explicitly ask for permission to remember it.

For example:
"धन्यवाद, रमेश। मैं आपका नाम और कुछ ज़रूरी जानकारी अगली बातचीत के लिए याद रख सकती हूँ। क्या आप चाहते हैं कि मैं इसे याद रखूँ?"

The caller must clearly say YES before anything is saved.

STEP 3 — CONSENT DECISION

If the caller clearly agrees, such as:
- yes
- हाँ
- sure
- okay
- you can remember it
- please remember it

THEN and ONLY THEN call save_caller_memory.

If the caller clearly declines, such as:
- no
- नहीं
- don't remember it
- don't save it
- I don't want that

DO NOT call save_caller_memory.

If the caller's response is ambiguous or unclear:
- Ask for confirmation.
- Do not save anything until clear consent is given.

IMPORTANT:
Merely learning someone's name is NOT consent.
Acknowledging someone's name is NOT consent.
The caller continuing the conversation is NOT consent.
Never assume consent.

STEP 4 — WHAT MAY BE SAVED

For Health Access, only save:
- name
- language preference
- age band
- ongoing condition
- last triage outcome

Never save:
- raw conversation transcripts
- written-out medical notes
- unnecessary medical details
- information that the caller did not consent to save

STEP 5 — AFTER CONSENT

After the caller explicitly agrees:
- Call save_caller_memory with only the information the caller agreed to remember.
- Do not save unrelated information.
- Do not claim that information was saved unless the tool succeeds.

If the caller refuses:
- Do not call save_caller_memory.
- Continue helping them normally.
- Do not repeatedly ask for consent during the same interaction unless they later provide new information they may want remembered.
MEMORY CONSENT — CRITICAL HEALTH ACCESS RULE

Never save any caller information without explicit permission.

This includes:
- Name
- Age or age band
- Language preference
- Ongoing health conditions
- Symptoms
- Previous health information
- Triage outcomes
- Any other personal or health-related fact

Whenever the caller provides new information that could be stored:

1. Do NOT call save_caller_memory yet.
2. First tell the caller what information you would like to remember.
3. Ask for explicit permission.
4. Only after the caller clearly says YES, call save_caller_memory.
5. If the caller says NO, do not save anything.
6. Never interpret silence, hesitation, "okay", "hmm", or unrelated answers as permission.
7. If permission is unclear, ask again.

Example:

Caller:
"My name is Ramesh and I have diabetes."

Assistant:
"Thank you, Ramesh ji. Would you like me to remember your name and that you have diabetes for future conversations?"

Caller:
"Yes."

Assistant:
"Thank you. I'll remember that for our future conversations."

→ NOW call save_caller_memory.

If caller says:
"No, don't remember it."

→ DO NOT call save_caller_memory.

IMPORTANT:
Do not save information first and ask for permission afterward.
Permission must ALWAYS come before the save function call.

HEALTH ACCESS PRIVACY:

Only save limited structured information relevant to this Health Access agent:
- name
- language preference
- age band
- ongoing condition
- last triage outcome

Never save raw conversation transcripts.
Never save written-out medical notes.
Never save unnecessary medical details.

LANGUAGE & SCRIPT:

LANGUAGE BEHAVIOR

Always reply in the same language style the user is currently speaking.

Rules:

1. If the user speaks English, respond in English.
   Example:
   User: "Hello"
   Assistant: "Hello! How can I help you today?"

2. If the user speaks Hindi, respond in Hindi using Devanagari script.
   Example:
   User: "नमस्ते"
   Assistant: "नमस्ते! मैं आपकी कैसे सहायता कर सकती हूँ?"

3. If the user speaks Hinglish, respond in natural Hinglish.
   Example:
   User: "Mujhe diabetes ke baare mein jaana hai."
   Assistant: "Bilkul, main aapko diabetes ke baare mein samjha sakti hoon."

4. Do not automatically translate English into Hindi.

5. Do not automatically translate Hindi into English.

6. Detect the user's current language from their latest message and mirror it.

7. If the user switches languages during the conversation, switch your response language too.

8. Do not force Hindi just because the user's previous conversations were in Hindi.

9. Keep the response natural and conversational rather than explicitly announcing the detected language.

ASSISTANT IDENTITY AND GENDER

You are ASHA Sathi, a female voice assistant.

Always refer to yourself using feminine Hindi grammar.

Use:
- "मैं कर सकती हूँ"
- "मैं समझ सकती हूँ"
- "मैं आपकी मदद कर सकती हूँ"
- "मैं बता सकती हूँ"

Never use masculine forms such as:
- "मैं कर सकता हूँ"
- "मैं समझ सकता हूँ"
- "मैं बता सकता हूँ"

GREETING

Match the user's language from their first meaningful utterance.

English:
User: "Hello"
Assistant: "Hello! How can I help you today?"

Hindi:
User: "नमस्ते"
Assistant: "नमस्ते! मैं आपकी कैसे सहायता कर सकती हूँ?"

Hinglish:
User: "Hello, mujhe health ke baare mein poochna hai."
Assistant: "Hello! Bilkul, aap bataiye, main aapki kaise help kar sakti hoon?"

DAY 5 — HEALTH FACILITY LOOKUP TOOL

You have access to a tool called get_nearby_health_facilities.

Use this tool whenever the caller asks about:
- nearby PHCs
- nearby hospitals
- nearby clinics
- health centres
- healthcare facilities
- where they can seek healthcare in a particular location

Do not answer with an invented facility name.

If the caller has not provided a location:
- Ask for their village, town, district, or area.
- Do not guess their location.

When the tool returns information:
- Explain the result naturally in the user's language.
- Do not read the JSON or raw tool output aloud.
- Mention that the information comes from live OpenStreetMap data when useful.
- Mention the retrieval time/date when relevant.
- Do not claim that a facility is open, available, or offering a particular service unless the tool data confirms it.

If the tool fails:
- Tell the caller that the live health facility information is temporarily unavailable.
- Do not invent or guess a facility.
- Offer to help with general health guidance instead.

Example:

User:
"Is there a PHC near Tonk?"

Assistant:
"Let me check the available health facility information for Tonk."

→ Call get_nearby_health_facilities.

After the tool returns:
Explain the relevant facilities naturally instead of reading the raw tool response.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."

    @function_tool()
    async def lookup_caller_memory(self, context: RunContext) -> str:
        """Look up the current caller's saved memory using their persistent user ID.

        Use this when starting a conversation to determine whether the caller
        has spoken with ASHA Sathi before.
        """

        participant = context.session.room_io.linked_participant

        if participant is None:
            return "No caller identity is available."

        logger.info("🔥 TOOL CALLED: lookup_caller_memory")
        user_id = participant.identity

        memory = lookup_caller(user_id)

        if memory is None:
            return "No saved memory exists for this caller. This is a new caller."

        return (
            "Saved caller memory found:\n"
            f"Name: {memory.get('name') or 'Not known'}\n"
            f"Language preference: "
            f"{memory.get('language_preference') or 'Not known'}\n"
            f"Facts: {memory.get('facts') or {}}\n"
            f"Last interaction: {memory.get('last_interaction') or 'Not known'}"
        )

    @function_tool()
    async def save_caller_memory(
        self,
        context: RunContext,
        name: str | None = None,
        language_preference: str | None = None,
        age_band: str | None = None,
        ongoing_condition: str | None = None,
        last_triage_outcome: str | None = None,
    ) -> str:
        """Save caller information ONLY after the caller has explicitly consented.

        Save only structured, limited Health Access information.
        Never save raw conversation transcripts or written-out medical notes.

        Args:
            name: The caller's name.
            language_preference: The caller's preferred language.
            age_band: The caller's broad age band, such as 18-30.
            ongoing_condition: A brief structured description of an ongoing condition.
            last_triage_outcome: A short structured triage outcome.
        """

        participant = context.session.room_io.linked_participant

        if participant is None:
            return "Unable to identify the caller, so nothing was saved."

        logger.info("🔥 TOOL CALLED: save_caller_memory")
        user_id = participant.identity

        facts = {}

        if age_band:
            facts["age_band"] = age_band

        if ongoing_condition:
            facts["ongoing_condition"] = ongoing_condition

        if last_triage_outcome:
            facts["last_triage_outcome"] = last_triage_outcome

        saved = save_caller(
            user_id=user_id,
            name=name,
            language_preference=language_preference,
            facts=facts,
        )

        return (
            f"Caller memory saved successfully for user_id {saved['user_id']}. "
            f"Saved name: {saved.get('name') or 'none'}. "
            f"Saved facts: {saved.get('facts') or {}}."
        )
        
    @function_tool()
    async def get_nearby_health_facilities(
        self,
        context: RunContext,
        location: str,
    ) -> str:
        """Find nearby healthcare facilities using live OpenStreetMap data.

        Use this tool whenever the caller asks about nearby:
        - hospitals
        - PHCs / Primary Health Centres
        - clinics
        - health centres
        - doctors
        - healthcare facilities

        If the caller gives a new location, always search using that
        new location. Never reuse results from another location.

        Do not invent facility names or locations.

        Args:
            location: User's location, e.g. "Tonk", "Jaipur".
        """

        logger.info(
            f"🔥 TOOL CALLED: get_nearby_health_facilities | "
            f"location={location}"
        )

        # ---------------------------------------------------------
        # 1. NORMALIZE LOCATION
        # ---------------------------------------------------------

        location_clean = location.strip()
        location_key = location_clean.lower()

        # Known locations
        HEALTH_LOCATION_COORDS = {
            "tonk": (26.1667, 75.7885),
            "tonk, rajasthan": (26.1667, 75.7885),

            "jaipur": (26.9124, 75.7873),
            "jaipur, rajasthan": (26.9124, 75.7873),
        }

        coords = HEALTH_LOCATION_COORDS.get(location_key)

        # Also handle common variants
        if coords is None:
            if "tonk" in location_key:
                coords = (26.1667, 75.7885)

            elif "jaipur" in location_key:
                coords = (26.9124, 75.7873)

        if coords:
            lat, lon = coords

            logger.info(
                f"📍 Using coordinates for {location_clean}: "
                f"lat={lat}, lon={lon}"
            )

        # ---------------------------------------------------------
        # 2. TRY LIGHTWEIGHT OVERPASS QUERY
        # ---------------------------------------------------------

        if coords:

            # IMPORTANT:
            # Smaller radius + nodes only = much lighter query.
            query = f"""
            [out:json][timeout:10];

            (
            node["amenity"="hospital"](around:5000,{lat},{lon});
            node["amenity"="clinic"](around:5000,{lat},{lon});
            node["amenity"="doctors"](around:5000,{lat},{lon});
            node["healthcare"="centre"](around:5000,{lat},{lon});
            node["healthcare"="clinic"](around:5000,{lat},{lon});
            node["healthcare"="hospital"](around:5000,{lat},{lon});
            );

            out tags;
            """

            overpass_urls = [
                "https://overpass-api.de/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter",
                "https://overpass.private.coffee/api/interpreter",
            ]

            headers = {
                "User-Agent": (
                    "ASHA-Sathi-Voice-Agent/1.0 "
                    "(healthcare-facility-search)"
                ),
                "Accept": "application/json",
            }

            # -----------------------------------------------------
            # Try Overpass servers one by one
            # -----------------------------------------------------

            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        connect=5.0,
                        read=12.0,
                        write=5.0,
                        pool=5.0,
                    )
                ) as client:

                    for url in overpass_urls:

                        try:
                            logger.info(
                                f"🌐 Trying Overpass server: {url}"
                            )

                            response = await client.post(
                                url,
                                data={"data": query},
                                headers=headers,
                            )

                            logger.info(
                                f"📡 Overpass response: "
                                f"{response.status_code} from {url}"
                            )

                            if response.status_code != 200:
                                logger.warning(
                                    f"⚠️ Overpass server failed: "
                                    f"{url} | "
                                    f"status={response.status_code}"
                                )
                                continue

                            data = response.json()

                            elements = data.get("elements", [])

                            logger.info(
                                f"📊 Overpass returned "
                                f"{len(elements)} elements"
                            )

                            facilities = []

                            seen_names = set()

                            for element in elements:

                                tags = element.get("tags", {})

                                name = tags.get("name")

                                if not name:
                                    continue

                                # Avoid duplicate facilities
                                name_key = name.strip().lower()

                                if name_key in seen_names:
                                    continue

                                seen_names.add(name_key)

                                facility_type = (
                                    tags.get("healthcare")
                                    or tags.get("amenity")
                                    or "health facility"
                                )

                                facilities.append(
                                    {
                                        "name": name.strip(),
                                        "type": facility_type,
                                    }
                                )

                                if len(facilities) >= 5:
                                    break

                            if facilities:

                                retrieved_at = datetime.now(
                                    timezone.utc
                                ).strftime(
                                    "%Y-%m-%d %H:%M UTC"
                                )

                                logger.info(
                                    f"✅ Found "
                                    f"{len(facilities)} facilities "
                                    f"for {location_clean}"
                                )

                                result = (
                                    f"Live healthcare facility data "
                                    f"retrieved from OpenStreetMap "
                                    f"via Overpass API at "
                                    f"{retrieved_at}.\n"
                                    f"Location: {location_clean}\n"
                                    f"Facilities:\n"
                                )

                                for facility in facilities:
                                    result += (
                                        f"- {facility['name']} "
                                        f"({facility['type']})\n"
                                    )

                                return result

                            logger.info(
                                f"⚠️ Overpass returned no named "
                                f"facilities for {location_clean}"
                            )

                        except httpx.TimeoutException:
                            logger.warning(
                                f"⚠️ Overpass timeout: {url}"
                            )
                            continue

                        except httpx.RequestError as e:
                            logger.warning(
                                f"⚠️ Overpass connection problem: "
                                f"{url} | {e}"
                            )
                            continue

                        except Exception as e:
                            logger.warning(
                                f"⚠️ Unexpected Overpass error: "
                                f"{url} | {e}"
                            )
                            continue

            except Exception as e:
                logger.warning(
                    f"⚠️ Overpass client setup failed: {e}"
                )

        # ---------------------------------------------------------
        # 3. NOMINATIM FALLBACK
        # ---------------------------------------------------------
        #
        # This is used only when Overpass is unavailable.
        #
        # Nominatim is also based on OpenStreetMap data and can
        # return named healthcare places.
        # ---------------------------------------------------------

        logger.info(
            f"🔄 Trying Nominatim fallback for {location_clean}"
        )

        nominatim_url = (
            "https://nominatim.openstreetmap.org/search"
        )

        nominatim_headers = {
            "User-Agent": (
                "ASHA-Sathi-Voice-Agent/1.0 "
                "(healthcare-facility-search)"
            ),
            "Accept": "application/json",
        }

        # Search terms that are useful for Indian healthcare
        search_query = (
            f"health centre, {location_clean}, Rajasthan, India"
        )

        try:

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=10.0,
                    write=5.0,
                    pool=5.0,
                )
            ) as client:

                response = await client.get(
                    nominatim_url,
                    params={
                        "q": search_query,
                        "format": "json",
                        "limit": 5,
                        "addressdetails": 1,
                    },
                    headers=nominatim_headers,
                )

                logger.info(
                    f"📡 Nominatim response: "
                    f"{response.status_code}"
                )

                response.raise_for_status()

                results = response.json()

                facilities = []

                seen_names = set()

                for item in results:

                    name = item.get("display_name")

                    if not name:
                        continue

                    # Take the first portion as the facility name
                    name_parts = name.split(",")

                    facility_name = name_parts[0].strip()

                    if not facility_name:
                        continue

                    name_key = facility_name.lower()

                    if name_key in seen_names:
                        continue

                    seen_names.add(name_key)

                    facilities.append(
                        {
                            "name": facility_name,
                            "type": "health centre",
                        }
                    )

                    if len(facilities) >= 5:
                        break

                if facilities:

                    retrieved_at = datetime.now(
                        timezone.utc
                    ).strftime(
                        "%Y-%m-%d %H:%M UTC"
                    )

                    logger.info(
                        f"✅ Nominatim found "
                        f"{len(facilities)} facilities "
                        f"for {location_clean}"
                    )

                    result = (
                        f"Live healthcare facility data "
                        f"retrieved from OpenStreetMap "
                        f"at {retrieved_at}.\n"
                        f"Location: {location_clean}\n"
                        f"Facilities:\n"
                    )

                    for facility in facilities:
                        result += (
                            f"- {facility['name']} "
                            f"({facility['type']})\n"
                        )

                    return result

        except httpx.TimeoutException:
            logger.warning(
                f"⚠️ Nominatim timeout for {location_clean}"
            )

        except httpx.RequestError as e:
            logger.warning(
                f"⚠️ Nominatim connection error: {e}"
            )

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"⚠️ Nominatim HTTP error: "
                f"{e.response.status_code}"
            )

        except Exception as e:
            logger.warning(
                f"⚠️ Nominatim fallback failed: {e}"
            )

        # ---------------------------------------------------------
        # 4. FINAL SAFE RESPONSE
        # ---------------------------------------------------------

        logger.error(
            f"❌ All healthcare facility sources failed "
            f"for location={location_clean}"
        )

        return (
            f"I am currently unable to retrieve live "
            f"healthcare facility information for "
            f"{location_clean}. "
            f"I don't want to guess or provide incorrect "
            f"facility details. Please try again shortly."
        )
server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3",language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Anjali",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
