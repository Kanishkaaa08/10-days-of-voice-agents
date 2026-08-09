import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

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
