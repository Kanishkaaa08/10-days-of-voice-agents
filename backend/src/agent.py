import asyncio
import logging
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from livekit import rtc
from prompt import SYSTEM_PROMPT
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
from call_analytics import record_call_outcome
from escalation import create_escalation as save_escalation
from escalation import get_active_escalation_for_caller
from memory import lookup_caller, save_caller

logger = logging.getLogger("agent")


class CallOutcomeTracker:
    """Tracks whether a call reached Asha Saathi's success condition."""

    def __init__(self) -> None:
        self.escalation_success = False

    def mark_escalation_success(self) -> None:
        self.escalation_success = True

    def determine_outcome(self, session: AgentSession) -> str:
        if self.escalation_success:
            return "SUCCESS"

        user_turns = 0
        agent_turns = 0

        for item in session.history.items:
            # Skip items that don't have text_content (e.g., AgentHandoff)
            if not hasattr(item, 'text_content'):
                continue
            
            text = item.text_content
            if not text or not text.strip():
                continue

            if item.role == "user":
                user_turns += 1
            elif item.role == "assistant":
                agent_turns += 1

        if user_turns > 0 and agent_turns > 0:
            return "SUCCESS"

        return "FAILURE"

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).


class Assistant(Agent):
    def __init__(self, outcome_tracker: CallOutcomeTracker | None = None) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._outcome_tracker = outcome_tracker

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

    @function_tool()
    async def create_escalation(
        self,
        context: RunContext,
        reason: str,
        summary: str,
        agent_checks: str,
        urgency: str,
        language: str,
        preferred_followup: str,
        caller_name: str | None = None,
    ) -> str:
        """Create a human-help escalation request.

        Call this tool when:
        - The caller agreed after you proactively offered human help for a red-flag
          symptom or diagnosis request, OR
        - The caller explicitly asked to speak to a human (treat as consent — no extra
          confirmation needed).

        Do NOT call if the caller refused human help or the situation does not warrant it.

        Do NOT include passwords, OTPs, PINs, account numbers, or
        authentication secrets in any field.

        Args:
            reason: Why human help is needed — red_flag_symptom, diagnosis_request,
                or explicit_human_help_request.
            summary: Short sanitized summary of the caller's concern.
            agent_checks: What the agent already asked or checked.
            urgency: Urgency level — high, medium, or low.
            language: Caller's preferred language.
            preferred_followup: How the caller wants to be contacted.
            caller_name: Caller's name if already known and consented.
        """

        participant = context.session.room_io.linked_participant

        if participant is None:
            return (
                "Unable to create escalation: caller identity not available. "
                "Do not tell the caller a request was created."
            )

        logger.info("🔥 TOOL CALLED: create_escalation | reason=%s", reason)
        user_id = participant.identity

        existing = get_active_escalation_for_caller(user_id)
        if existing:
            if self._outcome_tracker is not None:
                self._outcome_tracker.mark_escalation_success()

            reference_id = existing.get("reference_id", "unknown")
            status = existing.get("status", "Open")
            return (
                f"This caller already has an active human-help request. "
                f"Reference ID: {reference_id}. Status: {status}. "
                f"Do not create a duplicate. Tell the caller their existing reference ID."
            )

        if not caller_name:
            memory = lookup_caller(user_id)
            if memory and memory.get("name"):
                caller_name = memory["name"]

        try:
            result = save_escalation(
                caller_identifier=user_id,
                caller_name=caller_name,
                reason=reason,
                summary=summary,
                agent_checks=agent_checks,
                urgency=urgency,
                language=language,
                preferred_followup=preferred_followup,
            )
        except Exception:
            logger.exception("Failed to create escalation for user %s", user_id)
            return (
                "Escalation request could not be created due to a technical error. "
                "Do not tell the caller a request was created. "
                "Apologize and suggest they contact a healthcare facility directly."
            )

        if self._outcome_tracker is not None:
            self._outcome_tracker.mark_escalation_success()

        reference_id = result.get("reference_id", "unknown")
        return (
            f"Human-help request created successfully. "
            f"Reference ID: {reference_id}. "
            f"Status: Open. "
            f"Tell the caller their reference ID and that a qualified healthcare "
            f"professional will review their request. Do not promise immediate response."
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

    call_id = ctx.room.name
    logger.info("[ANALYTICS] Call started: call_id=%s", call_id)
    outcome_tracker = CallOutcomeTracker()

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

    async def record_call_analytics() -> None:
        logger.info("[ANALYTICS] Recording analytics triggered: call_id=%s", call_id)
        try:
            outcome = outcome_tracker.determine_outcome(session)
            logger.info("[ANALYTICS] Determined outcome: call_id=%s outcome=%s", call_id, outcome)
            logger.info("[ANALYTICS] Saving call analytics...")
            inserted = record_call_outcome(call_id, outcome)
            logger.info(
                "[ANALYTICS] Analytics record saved: call_id=%s outcome=%s inserted=%s",
                call_id,
                outcome,
                inserted,
            )
        except Exception:
            logger.exception("[ANALYTICS] Failed to record call analytics for call_id=%s", call_id)

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info("[ANALYTICS] Participant disconnected: call_id=%s participant=%s", call_id, participant.identity)
        # Record analytics when the participant (caller) disconnects
        asyncio.create_task(record_call_analytics())

    logger.info("[ANALYTICS] Analytics handlers registered: call_id=%s", call_id)

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
    logger.info("[ANALYTICS] Starting session: call_id=%s", call_id)
    await session.start(
        agent=Assistant(outcome_tracker=outcome_tracker),
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
    logger.info("[ANALYTICS] Session started: call_id=%s", call_id)

    # Join the room and connect to the user
    logger.info("[ANALYTICS] Connecting to room: call_id=%s", call_id)
    await ctx.connect()
    logger.info("[ANALYTICS] Connected to room: call_id=%s", call_id)


if __name__ == "__main__":
    cli.run_app(server)
