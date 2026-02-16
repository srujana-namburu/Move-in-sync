<div align="center">

# MoveInSync Fleet Management System

### AI-Powered Corporate Transportation Management Platform


[Features](#-features) • [Installation](#-installation) • [Documentation](#-documentation) • [API Reference](#-api-reference) • [Contributing](#-contributing)

</div>

<p align="center">
  <img src="https://github.com/user-attachments/assets/3dd33f0d-9774-4542-a852-574089fab8a2" alt="MoveInSync Dashboard" width="900"/>
</p>

---

## 📖 Overview

**MoveInSync** is a production-ready, AI-powered fleet management system designed for corporate employee transportation services. At its core is **Movi**, an intelligent AI assistant that enables fleet administrators to manage vehicles, routes, trips, and drivers through natural language conversations, voice commands, and even visual inputs.

Built with a modern tech stack combining **FastAPI**, **React**, **LangGraph**, and **OpenAI GPT-4**, this system transforms traditional fleet management into an intuitive, conversational experience while maintaining enterprise-grade safety through human-in-the-loop confirmations.

### 🎯 Key Highlights

- **Natural Language Interface**: Manage entire fleet operations through conversational AI
- **Voice-First Design**: Hands-free control via WebSocket-powered voice chat
- **Visual Intelligence**: Upload dashboard screenshots for GPT-4 Vision analysis
- **Smart Safety**: Human-in-the-loop confirmations for critical operations
- **Real-Time Routing**: OSRM-powered road-accurate route visualization
- **Context-Aware**: AI understands your current page and filters relevant tools
- **Production-Ready**: Docker support, CI/CD pipeline, comprehensive tests

---

## 🚀 Features

### AI Assistant (Movi)

- **Multi-Modal Input**: Text, voice, and image-based interactions
- **24+ Specialized Tools**: Domain-specific tools for trips, routes, vehicles, drivers, stops, and paths
- **LangGraph State Machine**: 4-node workflow with session persistence
- **Human-in-the-Loop**: Automatic approval requests for high-impact operations
- **Context Filtering**: Page-aware tool selection for improved accuracy
- **Streaming Responses**: Real-time token-by-token response generation

### Fleet Management

- **Trip Management**: Create, update, monitor daily trips with live status tracking
- **Vehicle Fleet**: Track buses and cabs with capacity, status, and assignments
- **Driver Registry**: Manage driver information and assignments
- **Route Planning**: Design routes with multiple stops and scheduling
- **Path Configuration**: Build reusable paths with ordered stop sequences
- **Deployment Tracking**: Link trips to specific vehicles and drivers

### Intelligent Confirmations

For destructive or high-impact operations, the AI:
1. Analyzes database consequences in real-time
2. Generates contextual warnings
3. Pauses execution via `interrupt()`
4. Resumes only after explicit user approval

**Protected Operations**:
- Trip deletions and critical updates
- Route status changes (active/inactive)
- Vehicle/driver removals from trips
- Deployment modifications

### User Experience

- **Modern UI**: Clean, responsive interface built with shadcn/ui and Tailwind CSS
- **Interactive Maps**: Mapbox GL with OSRM routing engine for accurate road-based routes
- **Real-Time Analytics**: Dashboard with fleet metrics and performance insights
- **Mobile-Responsive**: Optimized for desktop, tablet, and mobile devices
- **Dark Mode Ready**: UI components support theme switching

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  React 18 + TypeScript + Vite + shadcn/ui + TanStack Query │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API / WebSocket
┌────────────────────┴────────────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │          LangGraph AI Agent (Movi)                 │    │
│  │  ┌──────┐  ┌──────────┐  ┌─────────┐  ┌────────┐  │    │
│  │  │Intent│→ │Consequence│→ │Tool Call│→ │Response│  │    │
│  │  │ Node │  │   Node    │  │  Node   │  │  Node  │  │    │
│  │  └──────┘  └─────┬─────┘  └────┬────┘  └────────┘  │    │
│  │                  │ HITL        │ Exec               │    │
│  │                  │ Interrupt   │ Tools              │    │
│  │                  └─────────────┘                    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   24+      │  │  OpenAI Services │  │  SQLAlchemy    │ │
│  │ LangChain  │  │  - GPT-4o Vision │  │  ORM Layer     │ │
│  │   Tools    │  │  - GPT-4o-mini   │  │                │ │
│  │            │  │  - Whisper STT   │  │                │ │
│  │            │  │  - TTS (Nova)    │  │                │ │
│  └────────────┘  └──────────────────┘  └────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│              Database Layer (SQLite/PostgreSQL)             │
│  Stop • Path • Route • Vehicle • Driver • Trip • Deployment │
└─────────────────────────────────────────────────────────────┘
```

### LangGraph Agent Workflow

```mermaid
graph LR
    A[User Input] --> B[Intent Node]
    B --> C{High Impact?}
    C -->|Yes| D[Consequence Node]
    D --> E{User Approval?}
    E -->|No| F[Cancel]
    E -->|Yes| G[Tool Call Node]
    C -->|No| G
    G --> H[Response Node]
    H --> I[Final Answer]
```

**Flow Details**:

1. **Intent Node**: GPT-4o analyzes input (text/image), classifies intent, extracts entities, selects appropriate tool
2. **Consequence Node**: For high-impact tools, fetches DB consequences and triggers `interrupt()` for human approval
3. **Tool Call Node**: Executes the selected LangChain tool with normalized entity parameters
4. **Response Node**: GPT-4o-mini generates natural language summary of results

---

## 🛠️ Tech Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Web Framework** | FastAPI | High-performance async API server |
| **Database** | SQLAlchemy + SQLite/PostgreSQL | ORM and persistence layer |
| **AI Orchestration** | LangGraph + LangChain | Agent workflow and tool execution |
| **LLM Provider** | OpenAI | GPT-4o (vision), GPT-4o-mini (chat) |
| **Speech Services** | OpenAI Whisper + TTS | Voice transcription and synthesis |
| **Real-Time Comms** | WebSockets | Streaming responses and voice chat |
| **Schema Validation** | Pydantic v2 | Request/response validation |
| **Image Processing** | Pillow | Image handling for vision features |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | React 18 + TypeScript | UI library and type safety |
| **Build Tool** | Vite + SWC | Fast build and hot module replacement |
| **UI Components** | shadcn/ui (Radix UI) | Accessible component primitives |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **Maps** | Mapbox GL JS + OSRM | Interactive maps and route rendering |
| **State/Data Fetching** | TanStack React Query | Server state management |
| **Routing** | React Router DOM v6 | Client-side navigation |
| **Charts** | Recharts | Data visualization |
| **Forms** | react-hook-form + Zod | Form handling and validation |
| **Icons** | Lucide React | Icon library |
| **Markdown** | react-markdown + rehype | Chat message rendering |

### DevOps & Testing

- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Testing**: pytest (backend), Vitest (frontend planned)
- **Code Quality**: Black, ESLint, Prettier
- **Evaluation**: Custom evaluation suite with dataset

---

## 📦 Installation

### Prerequisites

Ensure you have the following installed:

- **Python** 3.10 or higher
- **Node.js** 18 or higher
- **npm** or **yarn**
- **Git**

### API Keys Required

- **OpenAI API Key**: For GPT-4, Whisper, and TTS ([Get API Key](https://platform.openai.com/api-keys))
- **Mapbox Access Token**: For map tiles ([Get Token](https://account.mapbox.com/access-tokens/))

---

### 🔧 Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/srujana-namburu/moveinsync.git
cd moveinsync
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=sqlite:///./moveinsync.db
EOF

# Run database migrations (tables auto-created on startup)
# Start the backend server
uvicorn main:app --reload --port 8000
```

**Backend will be available at**: `http://localhost:8000`
**API Documentation**: `http://localhost:8000/docs` (Swagger UI)

#### 3. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_MAPBOX_ACCESS_TOKEN=pk.your-mapbox-token-here
EOF

# Start development server
npm run dev
```

**Frontend will be available at**: `http://localhost:8080`

#### 4. Access the Application

1. Open your browser and navigate to `http://localhost:8080`
2. You'll be redirected to the login page
3. Register a new account or use demo credentials (if configured)
4. Start chatting with Movi in the dashboard!

---

### 🐳 Docker Deployment

#### Using Docker

```bash
# Build the Docker image
docker build -t moveinsync-backend .

# Run the container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key-here \
  --name moveinsync \
  moveinsync-backend
```

#### Using Docker Compose (Recommended)

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://user:password@db:5432/moveinsync
    depends_on:
      - db
    volumes:
      - ./backend:/app/backend

  frontend:
    build: ./frontend
    ports:
      - "8080:8080"
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_MAPBOX_ACCESS_TOKEN=${VITE_MAPBOX_ACCESS_TOKEN}
    volumes:
      - ./frontend/src:/app/src

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=moveinsync
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## 📚 Documentation

### AI Agent Tools

The system provides **24 specialized tools** organized by domain:

#### Bus Dashboard Tools (12 tools)

| Tool | Description |
|------|-------------|
| `get_all_trips` | List all daily trips with pagination |
| `get_trip_status` | Get live status of a specific trip |
| `get_trip_data` | Fetch detailed trip information |
| `create_new_trip` | Create a new daily trip |
| `update_trip` | Modify trip details (🔒 HITL) |
| `delete_trip` | Remove a trip (🔒 HITL) |
| `assign_vehicle_and_driver_to_trip` | Create deployment assignment |
| `remove_vehicle_from_trip` | Unassign resources (🔒 HITL) |
| `delete_deployment` | Delete assignment (🔒 HITL) |
| `list_all_vehicles` | Get vehicle fleet inventory |
| `get_unassigned_vehicles` | Find available vehicles |
| `list_all_drivers` | Get driver registry |

#### Stops & Paths Tools (7 tools)

| Tool | Description |
|------|-------------|
| `list_all_stops` | Get all geographic stops |
| `get_stop_details` | Fetch specific stop information |
| `create_new_stop` | Add new stop location |
| `update_stop` | Modify stop details |
| `list_all_paths` | Get all configured paths |
| `list_stops_for_path` | Get ordered stops for a path |
| `create_new_path` | Define new path with stop sequence |

#### Routes Tools (5 tools)

| Tool | Description |
|------|-------------|
| `list_all_routes` | Get all routes |
| `list_routes_using_path` | Find routes for a specific path |
| `find_routes_for_path` | Search routes by path |
| `create_new_route` | Create new route configuration |
| `update_route` | Modify route details (🔒 HITL) |
| `update_route_status` | Change route active status (🔒 HITL) |

🔒 **HITL** = Human-in-the-loop confirmation required

### Database Models

The system uses **6 core SQLAlchemy models** with relationships:

```python
# Core Entities
Stop          # Geographic points (lat, lon, name)
Path          # Ordered sequence of stops (via PathStop association)
Route         # Path + schedule + capacity + status
Vehicle       # Fleet vehicles (license_plate, type, capacity, status)
Driver        # Driver registry (name, phone)
DailyTrip     # Scheduled trip instance (route + date + booking%)
Deployment    # Assignment (trip ← vehicle + driver)
```

**Relationships**:
- `Path` ↔ `Stop`: Many-to-many via `PathStop` (with ordering)
- `Route` → `Path`: Many-to-one
- `DailyTrip` → `Route`: Many-to-one
- `Deployment` → `DailyTrip`, `Vehicle`, `Driver`: Many-to-one

---

## 🔌 API Reference

### Core Endpoints

#### AI Chat

```http
POST /movi/chat
Content-Type: application/json

{
  "message": "Show me all active routes",
  "session_id": "user-123",
  "context_page": "routes"
}

Response: NDJSON stream
{"type": "token", "content": "Here"}
{"type": "token", "content": " are"}
{"type": "confirmation", "payload": {...}}  # For HITL
{"type": "done"}
```

#### Voice Chat

```http
WebSocket: /movi/voice

# Client sends
{
  "type": "audio",
  "data": "base64_encoded_webm_audio"
}

# Server responds
{
  "type": "audio_response",
  "data": "base64_encoded_mp3",
  "text": "Transcribed response"
}
```

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/vehicles` | GET | List all vehicles |
| `/vehicles` | POST | Create vehicle |
| `/vehicles/{id}` | GET | Get vehicle details |
| `/vehicles/{id}` | PUT | Update vehicle |
| `/vehicles/{id}` | DELETE | Delete vehicle |
| `/drivers` | GET | List all drivers |
| `/drivers` | POST | Create driver |
| `/stops` | GET | List all stops |
| `/stops` | POST | Create stop |
| `/paths` | GET | List all paths |
| `/paths` | POST | Create path |
| `/routes` | GET | List all routes |
| `/routes` | POST | Create route |
| `/daily_trips` | GET | List all trips |
| `/daily_trips` | POST | Create trip |
| `/deployments` | GET | List all deployments |
| `/deployments` | POST | Create deployment |
| `/health` | GET | Health check |

**Full API Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

---

## 💬 Usage Examples

### Text-Based Interactions

```
User: "Show me all trips scheduled for today"
Movi: Here are today's scheduled trips:
      • Morning Shift - Electronic City Route (85% booked)
      • Evening Shift - Whitefield Route (92% booked)
      • Night Shift - HSR Layout Route (67% booked)

User: "Which vehicles are available for assignment?"
Movi: 3 unassigned vehicles are available:
      • KA-01-AB-1234 (Bus, 45 seats)
      • KA-02-CD-5678 (Bus, 52 seats)
      • KA-03-EF-9012 (Cab, 4 seats)

User: "Assign KA-01-AB-1234 to the morning shift with driver Ramesh"
Movi: ⚠️ This will assign:
      Vehicle: KA-01-AB-1234 (Bus, 45 seats)
      Driver: Ramesh Kumar (#D-042)
      Trip: Morning Shift - Electronic City Route

      Do you want to proceed? (yes/no)

User: "yes"
Movi: ✅ Successfully assigned! Vehicle KA-01-AB-1234 and driver
      Ramesh Kumar are now deployed for the Morning Shift.
```

### Image-Based Interactions

```
User: [Uploads screenshot with a trip circled]
      "Cancel this trip"

Movi: I can see you've highlighted "Evening Shift - Whitefield Route"
      (78% booked, 2 deployments).

      ⚠️ Deleting this trip will:
      • Cancel 39 passenger bookings
      • Free up 1 vehicle (KA-02-CD-5678)
      • Free up 1 driver (Suresh Reddy)

      Do you want to proceed? (yes/no)

User: "no, just deactivate it instead"
Movi: ✅ Route status changed to 'deactivated'. The trip remains in
      the system but won't accept new bookings.
```

### Voice Interactions

```
User: [Microphone] "How many buses are currently on trips?"
Movi: [Audio] "Currently, 12 buses are deployed across active trips.
       8 are on morning routes, 3 are on afternoon routes, and 1 is
       on standby."
```

---

## 🧪 Testing & Evaluation

### Run Unit Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Specific test suites
pytest tests/test_tools.py
pytest tests/test_langgraph_flow.py
pytest tests/test_crud_*.py
```

### Run Evaluation Suite

```bash
# Chat API evaluation
python evals/eval_chat.py

# Voice WebSocket evaluation (requires mock)
python evals/eval_voice.py
```

**Evaluation Dataset**: `evals/dataset.json` contains test scenarios covering:
- Trip management operations
- Vehicle and driver queries
- Route planning requests
- Edge cases and error handling

### CI/CD Pipeline

GitHub Actions automatically runs on every push/PR:

```yaml
# .github/workflows/ci.yml
- Install Python dependencies
- Run evaluation suite
- Check for regressions
```

---

## 🗂️ Project Structure

```
moveinsync/
│
├── backend/
│   ├── Agents/
│   │   ├── graph.py           # LangGraph state machine construction
│   │   ├── nodes.py           # 4 workflow nodes (intent, consequence, tool_call, response)
│   │   ├── state.py           # MoviState TypedDict definition
│   │   ├── tools.py           # 24 LangChain tool implementations
│   │   └── __init__.py
│   │
│   ├── crud/
│   │   ├── daily_trip.py      # Trip CRUD operations
│   │   ├── deployment.py      # Deployment CRUD
│   │   ├── driver.py          # Driver CRUD
│   │   ├── path.py            # Path CRUD
│   │   ├── route.py           # Route CRUD
│   │   ├── stop.py            # Stop CRUD
│   │   └── vehicle.py         # Vehicle CRUD
│   │
│   ├── routes/
│   │   ├── movi.py            # AI chat and voice token endpoints
│   │   ├── voice.py           # WebSocket voice handler
│   │   ├── vehicle.py         # Vehicle REST API
│   │   ├── driver.py          # Driver REST API
│   │   ├── stop.py            # Stop REST API
│   │   ├── path.py            # Path REST API
│   │   ├── route.py           # Route REST API
│   │   ├── daily_trip.py      # Trip REST API
│   │   └── deployment.py      # Deployment REST API
│   │
│   ├── utils/
│   │   └── audio_processing.py # OpenAI Whisper/TTS wrappers
│   │
│   ├── main.py                # FastAPI application entry point
│   ├── models.py              # SQLAlchemy ORM models
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── database.py            # Database engine and session management
│   └── requirements.txt       # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MoviAssistant.tsx      # Main AI chat panel component
│   │   │   ├── NavLink.tsx            # Navigation link component
│   │   │   ├── ShinyText.tsx          # Animated thinking indicator
│   │   │   ├── layout/
│   │   │   │   ├── DashboardLayout.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── TopNav.tsx
│   │   │   ├── map/
│   │   │   │   └── RouteMap.tsx       # Mapbox + OSRM route renderer
│   │   │   ├── modals/                # Dialog components
│   │   │   └── ui/                    # shadcn/ui library components
│   │   │
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   │   ├── Login.tsx
│   │   │   │   ├── Register.tsx
│   │   │   │   └── ForgotPassword.tsx
│   │   │   └── dashboard/
│   │   │       ├── BusDashboard.tsx   # Main trip management view
│   │   │       ├── ManageRoutes.tsx   # Route configuration
│   │   │       ├── StopsPaths.tsx     # Stop and path management
│   │   │       ├── Vehicles.tsx       # Vehicle fleet view
│   │   │       ├── Drivers.tsx        # Driver management
│   │   │       ├── Analytics.tsx      # Analytics dashboard
│   │   │       └── Settings.tsx       # App settings
│   │   │
│   │   ├── hooks/
│   │   │   ├── useVoiceChat.ts        # WebSocket voice chat hook
│   │   │   ├── use-toast.ts           # Toast notification hook
│   │   │   └── use-mobile.tsx         # Mobile detection hook
│   │   │
│   │   ├── types/                     # TypeScript type definitions
│   │   ├── lib/                       # Utility functions
│   │   ├── App.tsx                    # Root component with routing
│   │   └── main.tsx                   # React entry point
│   │
│   ├── public/                        # Static assets
│   ├── index.html                     # HTML template
│   ├── package.json                   # Node dependencies
│   ├── vite.config.ts                 # Vite configuration
│   ├── tsconfig.json                  # TypeScript configuration
│   └── tailwind.config.js             # Tailwind CSS configuration
│
├── evals/
│   ├── eval_chat.py                   # Chat API evaluation script
│   ├── eval_voice.py                  # Voice WebSocket evaluation
│   └── dataset.json                   # Test dataset
│
├── tests/
│   ├── conftest.py                    # Pytest fixtures
│   ├── test_chat_api.py               # Chat endpoint tests
│   ├── test_crud_path.py              # Path CRUD tests
│   ├── test_crud_route.py             # Route CRUD tests
│   ├── test_langgraph_flow.py         # LangGraph workflow tests
│   └── test_tools.py                  # Tool function tests
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI pipeline
│
├── dockerfile                         # Backend Docker image
├── .gitignore
└── README.md
```

---

## 🔧 Development

### Environment Variables

#### Backend (`.env`)

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key

# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./moveinsync.db
# For PostgreSQL: postgresql://user:password@localhost:5432/moveinsync

# Optional: LiveKit (for alternative voice implementation)
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret
```

#### Frontend (`.env`)

```bash
# Required
VITE_API_URL=http://localhost:8000
VITE_MAPBOX_ACCESS_TOKEN=pk.your-mapbox-token
```

### Code Style

**Backend**:
- Follow PEP 8 guidelines
- Use type hints for function signatures
- Use Black for code formatting: `black backend/`

**Frontend**:
- Use ESLint and Prettier
- Follow React best practices
- Run linter: `npm run lint`

### Adding New Tools

1. Define tool in `backend/Agents/tools.py`:

```python
from langchain.tools import tool

@tool
def your_new_tool(param1: str, param2: int) -> dict:
    """Tool description for the LLM."""
    # Implementation
    return {"status": "success", "data": result}
```

2. Add to `ALL_TOOLS` list and appropriate page filter in `tools.py`

3. If high-impact, add to `HIGH_IMPACT_TOOLS` in `nodes.py`

4. Write tests in `tests/test_tools.py`

### Database Migrations

Currently using auto-create on startup. For production, use Alembic:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```


## 🙏 Acknowledgments

### Technologies

- **OpenAI** - For GPT-4, Whisper, and TTS APIs
- **LangChain/LangGraph** - For AI agent orchestration framework
- **Vercel** - For shadcn/ui component library
- **Mapbox** - For beautiful map tiles
- **OSRM** - For open-source routing engine

## 👤 Author

**Srujana Namburu**

- GitHub: [@srujana-namburu](https://github.com/srujana-namburu)
- Repository: [moveinsync](https://github.com/srujana-namburu/moveinsync)

---


<div align="center">

**Built with ❤️ using FastAPI, React, and OpenAI**

⭐ Star this repo if you find it helpful!

[Report Bug](https://github.com/srujana-namburu/moveinsync/issues) • [Request Feature](https://github.com/srujana-namburu/moveinsync/issues) • [Documentation](#-documentation)

</div>
