import logging

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

Always respond in the caller's language when practical.

Hindi must always use Devanagari script.
Example: "नमस्ते", never "namaste".

English should remain in English.
Other languages should use their native script where supported.
"Namaste! I'm ASHA Sathi, your AI-powered healthcare support assistant for ASHA workers and frontline healthcare teams. I can help with symptom screening, maternal and child healthcare guidance, preventive care, and referral decisions. Which patient or health concern would you like assistance with today?"
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
