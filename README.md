# Clinic Slot Booking Agent

An AI-powered clinic appointment booking assistant built with FastAPI, LangGraph, Groq, Cal.com, Redis, and PostgreSQL.

The agent works like a clinic front-desk assistant. It checks appointment availability, collects patient details, confirms the booking, and creates the appointment through Cal.com.

## Features

- Conversational appointment booking flow
- Natural language date and time handling, such as "tomorrow at 3 PM"
- Cal.com availability checking
- Cal.com booking creation
- Redis-backed LangGraph conversation memory
- PostgreSQL conversation history storage
- FastAPI REST endpoints
- Pydantic request, response, and tool schemas
- Session-based conversations
- Fresh agent memory after each completed booking

## System Architecture

```mermaid
flowchart TD
    UserQuery["User Query"]
    ChatAPI["FastAPI /chat Endpoint"]
    SessionState["Session Thread Resolver"]
    AgentNode["LangGraph Agent Node"]
    SystemPrompt["Dynamic System Prompt"]
    GroqLLM["Groq LLM"]
    ToolDecision{"Tool Call Needed?"}
    AvailabilityTool["check_availability Tool"]
    BookingTool["create_slot Tool"]
    CalSlots["Cal.com Slots API"]
    CalBookings["Cal.com Bookings API"]
    ToolResult["Tool Result"]
    FinalResponse["Final Assistant Response"]
    HistoryAPI["GET /conversations/{session_id}"]

    subgraph Memory["Memory Layer"]
        Redis["Redis Checkpointer<br/>Short-Term Agent State"]
        Postgres["PostgreSQL<br/>Long-Term Conversation History"]
    end

    UserQuery --> ChatAPI
    ChatAPI --> SessionState
    SessionState --> AgentNode
    AgentNode --> SystemPrompt
    AgentNode --> GroqLLM
    GroqLLM --> ToolDecision

    ToolDecision -- "Check slots" --> AvailabilityTool
    ToolDecision -- "Create booking" --> BookingTool
    ToolDecision -- "No tool needed" --> FinalResponse

    AvailabilityTool --> CalSlots
    BookingTool --> CalBookings
    CalSlots --> ToolResult
    CalBookings --> ToolResult
    ToolResult --> AgentNode
    AgentNode --> FinalResponse

    SessionState -. "thread_id state" .-> Redis
    AgentNode -. "load / save state" .-> Redis
    FinalResponse -. "archive message" .-> Postgres
    HistoryAPI -. "read history" .-> Postgres

    classDef node fill:#1f2933,stroke:#8b949e,stroke-width:1px,color:#f8fafc;
    classDef decision fill:#253040,stroke:#c9d1d9,stroke-width:1px,color:#f8fafc;
    classDef memory fill:#30363d,stroke:#8b949e,stroke-width:1px,color:#f8fafc;
    classDef external fill:#182635,stroke:#58a6ff,stroke-width:1px,color:#f8fafc;

    class UserQuery,ChatAPI,SessionState,AgentNode,SystemPrompt,GroqLLM,AvailabilityTool,BookingTool,ToolResult,FinalResponse,HistoryAPI node;
    class ToolDecision decision;
    class Redis,Postgres memory;
    class CalSlots,CalBookings external;
```

## Booking Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant A as LangGraph Agent
    participant G as Groq LLM
    participant C as Cal.com
    participant R as Redis
    participant DB as PostgreSQL

    U->>API: Send message with session_id
    API->>A: Invoke graph with thread_id
    A->>R: Load conversation state
    A->>G: Interpret user intent

    alt User provides date/time
        A->>C: check_availability
        C-->>A: Available slots
        A-->>U: Ask for name, email, reason
    else Missing date/time
        A-->>U: Ask for preferred date and start time
    end

    U->>API: Provide details and confirmation
    API->>A: Continue booking flow
    A->>C: create_slot
    C-->>A: Booking confirmation
    A->>R: Save updated agent state
    API->>DB: Save human and AI messages
    A-->>U: Return booking details
```

1. User asks to book an appointment.
2. Agent asks for the appointment date and preferred time.
3. Agent calls `check_availability`.
4. If the requested slot is available, agent asks for patient name, email address, and reason for visit.
5. Agent reads the details back to the user for confirmation.
6. After confirmation, agent calls `create_slot`.
7. Cal.com creates the appointment.
8. Agent returns the final booking details.

After a booking is completed, the next booking request starts with fresh agent memory while keeping the same visible `session_id` for conversation history.

## Technology Stack

| Layer | Technology |
| --- | --- |
| API Framework | FastAPI |
| Agent Framework | LangGraph |
| LLM Integration | LangChain + Groq |
| LLM Provider | Groq |
| Tool Calling | LangChain tools |
| Booking Provider | Cal.com API |
| Agent Memory | Redis via `langgraph-checkpoint-redis` |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Data Validation | Pydantic |
| HTTP Client | HTTPX |
| Environment Config | python-decouple |
| Server | Uvicorn |
| Package Manager | uv / pip |

## Project Structure

```text
.
|-- agent/
|   `-- graph.py              # LangGraph agent and tool routing
|-- database/
|   |-- crud.py               # Database read/write helpers
|   |-- database.py           # SQLAlchemy engine and session
|   `-- models.py             # Conversation database model
|-- model/
|   `-- model.py              # Pydantic API, tool, and graph schemas
|-- prompt/
|   `-- prompt.py             # Dynamic system prompt
|-- tool/
|   |-- book_slot.py          # Cal.com booking tool
|   `-- check_availability.py # Cal.com availability tool
|-- config.py                 # Environment variable config
|-- main.py                   # FastAPI app and routes
|-- requirements.txt
|-- pyproject.toml
`-- README.md
```

## Tool Integration

### `check_availability`

Location: `tool/check_availability.py`

This tool checks available appointment slots from the Cal.com Slots API.

Input schema:

```json
{
  "date": "2026-08-25"
}
```

Returns the requested date, timezone, availability status, available slots, and error details if the Cal.com request fails.

### `create_slot`

Location: `tool/book_slot.py`

This tool creates a booking using the Cal.com Bookings API.

Input schema:

```json
{
  "start_time": "2026-08-26 15:00:00",
  "name": "Darshan",
  "email": "darshan@example.com",
  "reason": "Fever"
}
```

The tool converts appointment times to `Asia/Kolkata` when no timezone is provided.

## API Endpoints

FastAPI interactive docs are available after starting the server:

```text
http://localhost:8000/docs
```

### Chat

```http
POST /chat
```

Request:

```json
{
  "session_id": "lll",
  "user_message": "I want to book an appointment tomorrow at 3 PM"
}
```

Response:

```json
{
  "session_id": "lll",
  "user_message": "Sure, I will check availability for tomorrow at 3 PM."
}
```

### Conversation History

```http
GET /conversations/{session_id}
```

Example:

```text
GET /conversations/lll
```

Returns all stored human and AI messages for the session from PostgreSQL.

## Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=your_groq_model_name

CALCOM_KEY=your_calcom_api_key
CALCOM_EVENT=your_calcom_event_type_id

REDIS_URL=redis://username:password@host:port

DATABASE_URL=postgresql://username:password@host:port/database_name
```

Do not commit `.env` to GitHub. This project already includes `.env` in `.gitignore`.

## Installation

### Using uv

```bash
uv sync
```

Or install from `requirements.txt`:

```bash
uv pip install -r requirements.txt
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run The Application

```bash
uvicorn main:app --reload --port 8000
```

Open:

```text
http://localhost:8000/docs
```

## Example Conversation

```text
User: Hi
Agent: Hello Darshan! How can I assist you today?

User: I want to book an appointment.
Agent: Sure. Please share the date and preferred start time.

User: Tomorrow at 3 PM.
Agent: That slot is available. Please provide your full name, email, and reason for visit.

User: Name Darshan, email darshan@example.com, reason fever.
Agent: Please confirm the appointment details.

User: Confirm.
Agent: Your appointment has been successfully booked.
```

## Database

The app stores conversation history in PostgreSQL using SQLAlchemy.

Table: `conversations`

| Column | Description |
| --- | --- |
| `id` | Primary key |
| `session_id` | User session identifier |
| `Human_message` | User message |
| `AI_message` | Assistant response |
| `created_at` | Timestamp |

Tables are created automatically on app startup with:

```python
Base.metadata.create_all(bind=engine)
```

## Memory Management

LangGraph state is persisted in Redis using `AsyncRedisSaver`.

The API keeps the same user-facing `session_id`, but internally versions the LangGraph thread after each completed booking:

```text
{session_id}:booking:{completed_booking_count}
```

This prevents a completed appointment from leaking into the next appointment flow.

## Security Notes

- Keep `.env` private.
- Rotate API keys if they were accidentally committed or shared.
- Use HTTPS in production.
- Restrict database and Redis network access.
- Validate Cal.com event IDs before deployment.
- Avoid logging sensitive patient details in production.

## Future Improvements

- Add authentication for API clients
- Add structured booking status to the database
- Add automated tests for booking flow
- Add cancellation and rescheduling support
- Add email validation
- Add frontend chat UI
- Add Docker Compose for API, Redis, and PostgreSQL
