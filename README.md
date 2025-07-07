# 🤖 Codeaza Meeting Transcript Chatbot

An AI-powered assistant that helps you analyze meeting transcripts and answer context-aware questions like:

* Who participated in the meeting?
* What decisions were made?
* Can I get a summary of the discussion?
* What did a specific person say?

Built using **Google Gemini Flash 2.0**, **LangChain**, **FastAPI**, and deployed on **Vercel**.

---

## 🌐 Live Demo

* 🔗 **Frontend**: [codeaza-meeting-bot-frontend.vercel.app](https://codeaza-meeting-bot-frontend.vercel.app/)
* 🔗 **Backend API Docs**: [codeaza-meeting-bot-fastapibackend.vercel.app/docs](https://codeaza-meeting-bot-fastapibackend.vercel.app/docs)

---

## 📁 Repositories

* 🔙 **Backend**: [Codeaza--MeetingBot--fastapibackend](https://github.com/LearnCode801/Codeaza--MeetingBot--fastapibackend)
* 🔜 **Frontend**: [Codeaza--MeetingBot--frontend](https://github.com/LearnCode801/Codeaza--MeetingBot--frontend)

---

## 💡 Project Overview

Codeaza MeetingBot is a smart virtual assistant designed to process long meeting transcripts and help users extract actionable insights. It supports **multi-user sessions**, enabling different users to interact with the bot independently and simultaneously, with all their conversation history maintained per session.

The application is ideal for managers, teams, and organizations needing to revisit discussions, track decisions, and analyze who said what without reading entire transcripts.

---

## 🧠 AI Engine (Detailed Explanation)

The core intelligence of this system is powered by **Gemini Flash 2.0**—Google’s cutting-edge large language model—integrated via the `langchain-google-genai` wrapper. The LLM is configured with low temperature (0.3) to provide **concise, accurate, and deterministic responses** suitable for factual analysis of meeting content.

A **custom system prompt** is used to instruct the LLM to behave like a meeting analyst. This prompt is highly detailed, including instructions to:

* Identify all participants and their roles.
* Quote or paraphrase what each person said.
* Extract concrete decisions and outcomes.
* Provide structured summaries using bullet points.

To enhance conversation coherence, **LangChain’s `ConversationChain`** is employed with **`ConversationBufferMemory`**. This allows the AI to remember past user queries and responses, enabling truly **context-aware interactions** over a session.

Each time a user chats, the system:

1. Loads the corresponding meeting transcript.
2. Replays the session’s history into the LLM’s memory.
3. Injects the user’s latest query.
4. Generates a highly relevant and transcript-grounded response.

The prompt is dynamically rendered with the actual meeting transcript and user message for each interaction.

---

## 👥 Multi-User Session Support (How It Works)

This system is designed from the ground up to support **multiple users** interacting with the chatbot **in parallel**, without any data overlap or session conflict.

When a user uploads a transcript using the `/upload` endpoint, a unique `session_id` is either generated or provided. This `session_id` acts as a **container** for:

* The uploaded transcript
* Chat history (user + bot messages)
* Metadata like session creation and last activity time

All subsequent interactions (e.g., POST `/chat`) require this `session_id`. The backend uses this to:

* Retrieve that user’s transcript
* Retrieve and update their conversation history
* Keep their memory buffer in LangChain separate from others

This architecture ensures **strong isolation** between sessions. For example:

* User A can ask about *Marketing Meeting A*
* User B can ask about *Product Meeting B*
* Both receive accurate, independent, context-aware responses simultaneously

The session data is maintained in two locations:

* `sessions`: a global Python dictionary in the FastAPI backend storing transcripts and chat histories
* `session_memory`: a global dictionary storing LangChain memory objects, enabling in-memory conversation continuity

There are also endpoints for session management:

* `GET /sessions`: List all active sessions
* `GET /session/{session_id}`: Get session metadata
* `GET /session/{session_id}/history`: Get full chat history
* `DELETE /session/{session_id}`: Delete a specific session
* `POST /clear-all`: Wipe all sessions and memory (for development)

---

## 🚀 Tech Stack

| Component  | Technology                            |
| ---------- | ------------------------------------- |
| Backend    | Python, FastAPI                       |
| Frontend   | HTML, CSS, JavaScript                 |
| AI/LLM     | Google Gemini 2.0 Flash via LangChain |
| Memory     | LangChain `ConversationBufferMemory`  |
| Deployment | Vercel (Frontend + Backend)           |

---

## 📦 How to Run Locally

### Prerequisites

* Python 3.10+
* Node.js (for frontend if needed)
* Google Generative AI API Key

### Setup Instructions

1. **Clone the backend repo:**

   ```bash
   git clone https://github.com/LearnCode801/Codeaza--MeetingBot--fastapibackend
   cd Codeaza--MeetingBot--fastapibackend
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Google API Key:**
   Create a `.env` file:

   ```
   GOOGLE_API_KEY=your_google_genai_api_key
   ```

4. **Run the backend:**

   ```bash
   uvicorn server:app --reload
   ```

5. **(Optional) Run frontend:**
   Clone the frontend repo and deploy via Vercel or run locally.

---

## 📋 Sample Usage (Postman or Frontend)

1. **Upload transcript**

   ```json
   POST /upload
   {
     "transcript": "Alice: Welcome everyone...\nBob: Let's talk about sales...",
     "session_id": ""
   }
   ```

2. **Ask a question**

   ```json
   POST /chat
   {
     "session_id": "<returned_session_id>",
     "message": "Who participated in the meeting?"
   }
   ```


