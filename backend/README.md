# 🎙️ Asha Saathi — Voice AI Agent

> A real-time conversational voice agent built during the **10 Days of Voice Agents — VoiceForBharat Edition**, powered by **Murf Falcon**.

Asha Saathi started as a simple voice-agent experiment and gradually evolved into a complete voice AI system capable of having real-time conversations, following safety guardrails, remembering returning users, using tools, making outbound calls, escalating conversations to humans, tracking call outcomes, and handing conversations to specialist agents.

This repository contains my work and learnings from the 10-day voice-agent journey.

---

# 🌱 About Asha Saathi

Asha Saathi is a conversational voice agent designed to make interacting with AI more natural through voice.

Instead of typing a request into a traditional chatbot, users can simply speak with the agent.

The basic interaction is:

User speaks → Speech-to-Text → Agent/LLM → Tools/Memory → Murf Falcon TTS → Voice response

However, the goal of this project was not just to make an AI that could talk.

Over the 10-day challenge, I gradually added capabilities that made the agent more useful and closer to a real-world voice AI system.

These include:

- 🎙️ Real-time voice conversations
- 🧠 Persistent caller memory
- 🛡️ Personality and safety guardrails
- 🔧 Tool calling
- 📍 Healthcare facility lookup
- 📞 Outbound calling
- 👩‍💼 Human escalation
- 📊 Call analytics
- 🤝 Specialist-agent handoffs
- 🖥️ Real-time agent state in the frontend

---

# 🚀 My 10-Day Voice Agent Journey

## Day 1 — Building the First Voice Agent

### The Task

The first day was about understanding the basic building blocks of a voice agent and getting a real-time conversation working.

The core components were:

- Speech-to-Text
- LLM
- Text-to-Speech
- Real-time audio transport

### What I Built

I started building Asha Saathi as a real-time voice agent.

The first version followed a simple pipeline:

```text
User speaks
     ↓
Speech-to-Text
     ↓
LLM
     ↓
Text-to-Speech
     ↓
User hears response
````

This was the foundation for everything that came later.

I used LiveKit for real-time communication, Deepgram for speech recognition, Google Gemini as the LLM layer, and Murf Falcon for voice generation.

The main goal on Day 1 was simply:

> Get an AI agent that can listen, think, and speak back in real time.

---

## Day 2 — Giving the Agent a Personality

### The Task

A voice agent should not sound like a generic AI model.

The task was to define the agent's identity, personality, objectives, and conversational behaviour.

### What I Built

I created a dedicated system prompt for Asha Saathi.

Instead of relying on the default behaviour of the LLM, I defined:

* Who Asha Saathi is
* How the agent should communicate
* What kind of help it should provide
* How it should respond to users
* How it should handle unclear requests
* What its overall objectives are

This was an important change because the agent started feeling less like an LLM with a voice and more like an actual assistant.

---

## Day 3 — Adding Guardrails

### The Task

A useful AI agent needs boundaries.

The goal was to make sure the agent would not blindly answer every request and would behave safely when a situation was outside its scope.

### What I Built

I added behavioural and safety guardrails to Asha Saathi.

The agent was given clear instructions about:

* What it can and cannot help with
* How it should handle uncertain situations
* When it should ask for clarification
* When it should avoid unsupported claims
* When it should stop trying to handle something itself
* When it should escalate a conversation

This became especially important later when I added tools, memory, human escalation, and specialist agents.

One of the biggest lessons from this stage was that:

> A good agent is not one that answers everything. A good agent also knows when it should not answer.

---

## Day 4 — Giving Asha Saathi Memory

### The Task

A voice assistant becomes much more useful when returning users don't have to repeat information they have already shared.

The goal was to introduce memory into the agent.

### What I Built

I implemented persistent caller memory.

Asha Saathi can look up information associated with a returning caller and use relevant information during the conversation.

The memory system can work with structured information such as:

* Caller name
* Language preference
* Limited caller facts
* Previous interaction information

The memory flow is:

```text
Caller
  ↓
Identify caller
  ↓
Look up saved memory
  ↓
Use relevant context
  ↓
Conversation
  ↓
Explicit consent
  ↓
Save limited structured information
```

I also made the memory flow consent-aware and avoided treating the entire conversation transcript as something that should automatically be stored.

This was my first step toward making the agent feel like it could actually remember its users rather than starting from zero every time.

---

## Day 5 — Giving the Agent Tools

### The Task

An LLM can generate answers, but it cannot automatically know current external information.

The goal was to make Asha Saathi capable of using tools when it needed additional information or wanted to perform an action.

### What I Built

I added function tools that the agent can call when required.

One of the important tools I implemented allows Asha Saathi to find nearby healthcare facilities using live OpenStreetMap data.

The tool can search for:

* Hospitals
* Clinics
* Doctors
* Health centres
* Healthcare facilities

The flow became:

```text
User asks for information
        ↓
Asha Saathi understands the request
        ↓
Agent decides a tool is required
        ↓
Healthcare facility lookup
        ↓
Live OpenStreetMap data
        ↓
Tool result
        ↓
Asha Saathi explains the result through voice
```

This changed the way I thought about the LLM.

The LLM wasn't the whole application anymore.

It became the reasoning layer that could decide when to use other parts of the system.

---

## Day 6 — Making the Agent More Real-Time and Reliable

### The Task

As more components were added, the voice pipeline became more complex.

The goal was to improve the overall real-time experience and make the different parts of the system work together reliably.

### What I Worked On

I worked on the interaction between:

* Frontend
* LiveKit
* Speech-to-Text
* LLM
* Tools
* Text-to-Speech

At this point I started running into practical problems involving:

* API configuration
* Real-time connections
* Audio flow
* Server behaviour
* Latency
* Error handling

This was one of the days where debugging became as important as development.

Instead of looking at the whole system as one large problem, I learned to debug it layer by layer:

```text
Frontend
   ↓
Audio connection
   ↓
Speech-to-Text
   ↓
Agent / LLM
   ↓
Tool execution
   ↓
Text-to-Speech
   ↓
Audio output
```

This made it much easier to identify where something was actually failing.

---

## Day 7 — Outbound Voice Calls

### The Task

A voice agent should not necessarily be limited to a user opening a browser and clicking a microphone button.

The goal was to explore outbound phone conversations.

### What I Built

I added an outbound calling workflow using Twilio along with the existing voice-agent infrastructure.

This allowed Asha Saathi to move from a browser-only interaction toward a phone-based voice workflow.

The architecture became:

```text
Outbound Call
      ↓
Telephony
      ↓
Voice Agent
      ↓
Speech-to-Text
      ↓
LLM / Agent
      ↓
Murf Falcon
      ↓
Voice conversation
```

This introduced new challenges around call lifecycle, connection handling, user context, and call outcomes.

It also made the project feel much closer to a real voice-agent application rather than a browser demo.

---

## Day 8 — Human Escalation and Call Analytics

### The Task

AI should not always try to solve everything on its own.

The goal was to add a way for Asha Saathi to involve a human when necessary and also track what happened during conversations.

### What I Built

I implemented a human escalation flow.

When the agent determines that a conversation should not continue entirely through AI, it can create an escalation for human support.

The flow is:

```text
User
 ↓
Asha Saathi
 ↓
Can AI safely handle this?
 ├── Yes → Continue
 │
 └── No → Escalate
              ↓
         Human support
```

I also implemented call outcome tracking and a call analytics dashboard.

Instead of only checking whether the agent was technically working, I could now look at the outcome of conversations.

This introduced an important concept:

> Building an AI agent is not only about making it work. You also need visibility into what happened during its conversations.

---

## Day 9 — Specialist Agent Handoff

### The Task

The goal was to make the system more modular by allowing the main agent to hand conversations to another agent when specialist knowledge or behaviour was required.

### What I Built

I added a specialist-agent workflow with a **Clinic Specialist**.

Instead of building one huge agent that handles every possible situation, Asha Saathi can recognize when a request should be handled by a specialist.

The flow is:

```text
                    User
                      ↓
                Asha Saathi
                      ↓
               Understand intent
                      ↓
             Specialist required?
                ↙           ↘
              No             Yes
               ↓              ↓
           Continue      Clinic Specialist
                              ↓
                     Continue with context
```

The important part of a handoff is not simply switching agents.

The specialist needs enough context to continue the conversation naturally so that the user doesn't have to explain everything again.

This was one of the most interesting parts of the challenge because it introduced me to the idea of building systems where multiple agents can work together.

---

## Day 10 — Sharing the Journey

### The Task

The final day was about documenting the project and sharing what was learned during the challenge.

Instead of building another major feature, I focused on turning the work from the previous nine days into something another developer could understand and learn from.

### What I Did

For Day 10, I prepared:

* Project documentation
* This GitHub README
* The final architecture explanation
* Setup and installation instructions
* A technical blog
* Project/demo links
* A LinkedIn post sharing the journey

The goal is to make the project understandable not only to someone looking at the final application, but also to someone who wants to build their own voice agent.

---

# 🧠 Final System

After ten days, the project had evolved from a basic voice pipeline into a complete voice-agent system.

The final flow can be summarized as:

```text
                         USER
                           │
                           ▼
                    Voice / Phone
                           │
                           ▼
                  Real-Time Transport
                           │
                           ▼
                    Speech-to-Text
                           │
                           ▼
                   ┌───────────────┐
                   │ Asha Saathi   │
                   │    Agent      │
                   └───────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
         Memory          Tools       Guardrails
                           │
                           ▼
                 Healthcare Lookup
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
       Human Escalation            Clinic Specialist
            │                             │
            └──────────────┬──────────────┘
                           │
                           ▼
                      Agent Response
                           │
                           ▼
                    Murf Falcon TTS
                           │
                           ▼
                    Voice Response
                           │
                           ▼
                         USER

                   ┌─────────────────┐
                   │ Call Analytics  │
                   └─────────────────┘
```

---

# ✨ Final Features

| Feature                | Description                                     |
| ---------------------- | ----------------------------------------------- |
| 🎙️ Real-time voice    | Users can have natural voice conversations      |
| 🗣️ Speech recognition | Converts user speech into text                  |
| 🔊 Murf Falcon         | Generates fast, natural voice responses         |
| 🧠 LLM reasoning       | Understands requests and decides what to do     |
| 🛡️ Guardrails         | Controls agent behaviour and safety             |
| 🧠 Memory              | Remembers limited structured caller information |
| 🔧 Tools               | Allows the agent to retrieve useful information |
| 📍 Healthcare lookup   | Searches live healthcare facilities             |
| 📞 Outbound calls      | Supports phone-based voice interactions         |
| 👩‍💼 Human escalation | Allows conversations to be escalated            |
| 📊 Analytics           | Tracks call outcomes                            |
| 🤝 Specialist handoff  | Transfers conversations to specialist agents    |

---

# 🛠️ Tech Stack

## AI & Voice

* **Murf Falcon** — Text-to-Speech
* **Deepgram** — Speech-to-Text
* **Google Gemini** — LLM
* **LiveKit Agents** — Voice-agent framework
* **LiveKit** — Real-time audio transport

## Backend

* Python
* FastAPI
* HTTPX
* LiveKit Agents
* Twilio

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* LiveKit Client

## Data & External Services

* OpenStreetMap
* Overpass API
* Nominatim
* LiveKit
* Murf
* Deepgram
* Google Gemini
* Twilio

---

# 📁 Project Structure

```text
10-days-of-voice-agents/
│
├── backend/
│   ├── src/
│   │   ├── agent.py
│   │   ├── api_server.py
│   │   ├── call_analytics.py
│   │   ├── clinic_specialist.py
│   │   ├── escalation.py
│   │   ├── memory.py
│   │   ├── outbound_prompt.py
│   │   ├── prompt.py
│   │   └── twilio_server.py
│   │
│   ├── tests/
│   ├── .env.example
│   └── pyproject.toml
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── public/
│   ├── .env.example
│   └── package.json
│
├── start_app.sh
├── start_app.ps1
├── .gitignore
└── README.md
```

---

# 💻 Requirements

Before running the project, make sure you have:

* Python 3.10+
* Node.js 18+
* npm
* pnpm
* uv
* A LiveKit project
* Internet connection for external APIs

Depending on which features you want to use, you will also need API credentials for:

* Murf
* LiveKit
* Deepgram
* Google Gemini
* Twilio

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/Kanishkaaa08/10-days-of-voice-agents.git

cd 10-days-of-voice-agents
```

---

## 2. Install uv

### Windows

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 3. Install pnpm

```bash
npm install -g pnpm
```

---

# 🔐 Environment Variables

The project uses environment variables for API credentials.

Create:

```text
backend/.env.local
```

and:

```text
frontend/.env.local
```

Use the existing `.env.example` files as a reference.

A typical backend configuration will look like:

```env
MURF_API_KEY=your_murf_api_key

LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

DEEPGRAM_API_KEY=your_deepgram_api_key

GOOGLE_API_KEY=your_google_api_key
```

For outbound calling, configure the required Twilio credentials in your local environment.

### ⚠️ Never expose secrets

Do not commit:

```text
.env
.env.local
API keys
API secrets
Twilio credentials
Private phone numbers
Caller information
```

Only placeholder values should be present in `.env.example`.

---

# 📦 Backend Setup

```bash
cd backend
```

Install dependencies:

```bash
uv sync
```

Return to the project root:

```bash
cd ..
```

---

# 📦 Frontend Setup

```bash
cd frontend
pnpm install
```

Return to the project root:

```bash
cd ..
```

---

# ▶️ Running the Application

## Windows

From the project root:

```powershell
.\start_app.ps1
```

## macOS / Linux

```bash
chmod +x start_app.sh
./start_app.sh
```

---

# 🖥️ Running Backend and Frontend Separately

If you prefer to run the services separately:

### Backend

```bash
cd backend

uv run python src/agent.py dev
```

### Frontend

Open another terminal:

```bash
cd frontend

pnpm dev
```

Then open:

```text
http://localhost:3000
```

Allow microphone access and start a conversation with Asha Saathi.

---

# 🧪 Testing the Agent

After starting the application, test the features one by one.

### 1. Basic Conversation

Try:

```text
Hello, who are you?
```

### 2. Tool Usage

Try asking:

```text
Can you find healthcare facilities near Tonk?
```

### 3. Memory

Test a conversation where the caller provides information and explicitly allows relevant information to be remembered.

Then test the same caller again and verify that the agent can retrieve the stored context.

### 4. Human Escalation

Test a situation that should be passed to human support.

### 5. Specialist Handoff

Test a request that should be handled by the Clinic Specialist.

### 6. Analytics

After a call, check whether the conversation outcome appears in the analytics dashboard.

---

# 🔒 Privacy and Security

This project uses external APIs and voice communication, so protecting credentials and user information is important.

Before making the repository public:

* Remove all real API keys
* Remove private phone numbers
* Remove real caller information
* Avoid committing raw conversation data
* Keep `.env.local` out of Git
* Use `.env.example` for configuration templates
* Blur private information in any public demo

---

# 🧩 Challenges I Faced

The project was not built without problems.

One of the biggest challenges was getting several real-time components to work together:

```text
Frontend
   ↓
LiveKit
   ↓
Speech-to-Text
   ↓
LLM
   ↓
Tools / Memory
   ↓
Murf Falcon
   ↓
LiveKit
   ↓
Frontend
```

When something failed, it was not always obvious which layer was responsible.

I learned to debug each layer independently instead of treating the entire voice agent as one system.

Another challenge was API configuration. With multiple services involved, a missing or incorrect environment variable could make the entire pipeline appear broken.

The specialist handoff also required more thought than I initially expected. Passing control to another agent is easy; passing enough context for the conversation to continue naturally is the harder part.

---

# 📚 What I Learned

The biggest lesson from the challenge was:

> **A voice agent is much more than STT + LLM + TTS.**

Those components create the basic voice pipeline, but a useful agent needs much more around them.

I learned about:

* Voice pipeline design
* Real-time communication
* Prompt and personality design
* AI guardrails
* Persistent memory
* Tool calling
* External API integration
* Outbound voice calls
* Human escalation
* Call analytics
* Multi-agent handoffs
* Debugging real-time AI systems

I started this challenge thinking about:

```text
"How can I make an AI talk?"
```

By the end, I was thinking about:

```text
"How can I build an AI system that can
listen, understand, remember, act,
communicate, escalate, and collaborate?"
```

That change in perspective was probably the most valuable part of the challenge.

---

# 🔮 Future Improvements

There are several things I would like to improve in the next version:

* Better multilingual and code-mixed conversations
* More specialist agents
* Improved long-term memory
* Better conversation evaluation
* Latency monitoring
* More detailed analytics
* Better error recovery
* Production deployment
* More real-world integrations

---

# 🔗 Resources

* [Murf AI](https://murf.ai/)
* [Murf Falcon Documentation](https://murf.ai/api/docs/text-to-speech-models/falcon-2)
* [LiveKit Voice AI Quickstart](https://docs.livekit.io/agents/start/voice-ai/)
* [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
* [Deepgram Documentation](https://developers.deepgram.com/)
* [Google Gemini API Documentation](https://ai.google.dev/)
* [Twilio Documentation](https://www.twilio.com/docs)
* [OpenStreetMap](https://www.openstreetmap.org/)

---

# 🏆 10 Days of Voice Agents — VoiceForBharat Edition

Asha Saathi was built as part of the:

**10 Days of Voice Agents — VoiceForBharat Edition**

Across 10 days, the project evolved from a basic voice conversation into a complete voice-agent system with:

```text
🎙️ Voice
   +
🧠 Memory
   +
🛡️ Guardrails
   +
🔧 Tools
   +
📞 Outbound Calls
   +
👩‍💼 Human Escalation
   +
📊 Analytics
   +
🤝 Specialist Handoff
```

**Powered by Murf Falcon.**

---

# 👩‍💻 Author

**Kanishka Mathur**

B.Tech — Artificial Intelligence

GitHub:
[https://github.com/Kanishkaaa08](https://github.com/Kanishkaaa08)

---

# 📄 License

This project is licensed under the MIT License.

