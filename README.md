# BuildTrack AI MVP

A conversational AI assistant for construction site entry management.

## Features

- **Material entries** - cement, steel, sand, bricks, epoxy, concrete, aggregate, grout
- **Labour entries** - mason, carpenter, steel fixer, electrician, plumber, painter, helper
- **Equipment entries** - JCB, crane, excavator, mixer, roller, drill machine
- Natural language parsing (regex-based, no AI required)
- Multi-turn conversation to collect missing fields
- Session memory across conversation turns
- Progress tracking
- Confirmation & save flow
- JSON file storage

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic
- Regex-based NLP (no external AI dependencies)

## Project Structure

```
mvp/
├── main.py                     # FastAPI app & endpoints
├── parser/
│   ├── intent_parser.py        # Entry type detection
│   ├── material_parser.py      # Material field extraction
│   ├── labour_parser.py        # Labour field extraction
│   └── equipment_parser.py     # Equipment field extraction
├── memory/
│   └── session_manager.py      # Session storage & retrieval
├── models/
│   └── schemas.py              # Pydantic request/response models
├── data/
│   ├── materials.py            # Material/brand dictionaries
│   ├── labour_types.py         # Labour type dictionaries
│   └── equipment.py            # Equipment dictionaries
├── utils/
│   ├── field_checker.py        # Missing field detection & progress
│   └── question_generator.py   # Question & summary generation
├── storage/
│   ├── sessions.json           # Active session state
│   └── saved_entries.json      # Completed saved entries
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the server

```bash
uvicorn main:app --reload
```

Server starts at `http://localhost:8000`

### 3. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/chat` | Send a message |
| GET | `/session/{id}` | Get session state |
| POST | `/reset/{id}` | Reset session |

### 4. Example Usage

#### Material Entry

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "Bought 500kg cement"}'
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "Sunrise Tower"}'
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "ABC Traders"}'
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "450"}'
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "2"}'
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "Foundation"}'
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "yes"}'
```

#### Labour Entry

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test2", "message": "Added 12 masons"}'
```

#### Equipment Entry

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test3", "message": "JCB worked 6 hours"}'
```

#### Check Session State

```bash
curl http://localhost:8000/session/test1
```

#### Reset Session

```bash
curl -X POST http://localhost:8000/reset/test1
```

## Response Fields

| Field | Description |
|-------|-------------|
| `session_id` | Unique session identifier |
| `status` | `incomplete`, `completed`, `saved`, `cancelled`, `unknown`, `error` |
| `entry_type` | `material`, `labour`, `equipment` |
| `message` | AI response message |
| `extracted` | Extracted field values |
| `missing_fields` | Fields still needed |
| `current_question` | Next question to ask |
| `progress` | Percentage complete (0-100) |
| `confidence` | Parsing confidence score (0-1) |
| `entities` | List of extracted entities |
| `summary` | Entry summary (shown at completion) |

## Architecture Flow

```
User → FastAPI → Parser → Session Memory → Missing Field Detector → Question Generator → JSON Response
```
