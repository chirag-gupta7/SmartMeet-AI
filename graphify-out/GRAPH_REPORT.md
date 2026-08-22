# Graph Report - SmartMeet AI  (2026-08-22)

## Corpus Check
- Corpus is ~13,798 words - fits in a single context window. You may not need a graph.

## Summary
- 366 nodes · 545 edges · 25 communities (22 shown, 3 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 30 edges (avg confidence: 0.87)
- Token cost: 4,200 input · 6,800 output

## Community Hubs (Navigation)
- Data Models & Calendar Routes
- Command Processor Rationale
- Frontend App & Components
- NLP Parsing Services
- Audio Processing
- Frontend Package Metadata
- Backend Deps & Auth Docs
- Frontend Dev Dependencies
- Voice Routes & TTS
- Frontend Runtime Deps
- Auth & User Model
- External Integrations
- App Factory & Config
- Architecture Overview
- DB Migrations Env
- PWA Manifest
- Voice Command Parsing
- HuggingFace Dependency
- Dateutil Dependency
- Requests Dependency

## God Nodes (most connected - your core abstractions)
1. `VoiceCommandProcessor` - 25 edges
2. `User` - 11 edges
3. `useAuth()` - 11 edges
4. `Meeting` - 10 edges
5. `create_structured_event()` - 10 edges
6. `get_calendar_service()` - 9 edges
7. `sync_calendar()` - 8 edges
8. `ModernAudioProcessor` - 8 edges
9. `create_app()` - 7 edges
10. `list_events()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `React Frontend (Tailwind UI)` --semantically_similar_to--> `React SPA Frontend`  [INFERRED] [semantically similar]
  README.md → docs/architecture.md
- `Flask Backend API` --semantically_similar_to--> `Flask REST API Backend`  [INFERRED] [semantically similar]
  README.md → docs/architecture.md
- `google-generativeai >=0.8.3` --semantically_similar_to--> `OpenAI Service Integration`  [INFERRED] [semantically similar]
  backend/requirements.txt → docs/architecture.md
- `OpenAI Integration Hook` --references--> `google-generativeai >=0.8.3`  [AMBIGUOUS]
  README.md → backend/requirements.txt
- `python-dotenv 1.0.1` --conceptually_related_to--> `Env-Var Service Plug-in Pattern`  [INFERRED]
  backend/requirements.txt → docs/architecture.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Login/Register Flow Participants (Hashing + JWT)** — docs_architecture_login_register_flow, docs_architecture_bcrypt_password_hashing, docs_architecture_jwt_token_persistence, backend_requirements_flask_bcrypt, backend_requirements_flask_jwt_extended [INFERRED 0.85]
- **Voice-to-Meetings Scheduling Pipeline** — docs_architecture_meeting_scheduling_flow, docs_architecture_web_speech_api, docs_architecture_voice_process_endpoint, docs_architecture_meetings_endpoint, docs_architecture_meeting_model [INFERRED 0.90]
- **External Services Plugged In via Environment Variables** — docs_architecture_env_service_plugin_pattern, docs_architecture_openai_service, docs_architecture_google_calendar_service, docs_architecture_sendgrid_notifications, docs_architecture_firebase_fcm [EXTRACTED 1.00]

## Communities (25 total, 3 thin omitted)

### Community 0 - "Data Models & Calendar Routes"
Cohesion: 0.08
Nodes (39): BaseModel, Log, Meeting, Note, datetime, _build_form_sections(), create_structured_event(), event_form_definition() (+31 more)

### Community 1 - "Command Processor Rationale"
Cohesion: 0.07
Nodes (22): Any, Log command events to database, ensuring application context., Get the current weather for a location using OpenWeatherMap API., Get top headlines (placeholder for real news API integration)., Set a reminder for a future time., Set a timer for a specified duration., Enhanced voice command processor with real API integrations. Supports weather,…, Background task to track a timer and mark it complete when done. (+14 more)

### Community 2 - "Frontend App & Components"
Cohesion: 0.09
Nodes (21): App(), Layout(), OAuthCallback(), ProtectedRoute(), VoiceInput(), AuthContext, AuthProvider(), useAuth() (+13 more)

### Community 3 - "NLP Parsing Services"
Cohesion: 0.15
Nodes (23): create_event_manual_parse(), Manually parses conversation text to create a calendar event. This is a…, Flask, Sets the Flask app instance for use in command processor background tasks., set_flask_app_for_command_processor(), parse_natural_language_datetime(), Parse natural language datetime expressions. Returns a dictionary with the…, authenticate_google_calendar() (+15 more)

### Community 4 - "Audio Processing"
Cohesion: 0.08
Nodes (18): add(), lin2ulaw(), ModernAudioProcessor, mul(), ratecv(), Modern Audio Processing Module - Python 3.13 Compatible Replaces deprecated…, Modern replacement for audioop.lin2ulaw Convert linear samples to u-law encoding, Modern replacement for audioop.ulaw2lin Convert u-law samples to linear encoding (+10 more)

### Community 5 - "Frontend Package Metadata"
Cohesion: 0.08
Nodes (24): author, browserslist, development, production, description, eslintConfig, extends, license (+16 more)

### Community 6 - "Backend Deps & Auth Docs"
Cohesion: 0.12
Nodes (20): elevenlabs 1.9.0, Flask 3.0.0, Flask-Bcrypt 1.0.1, Flask-Cors 4.0.0, Flask-JWT-Extended 4.6.0, Flask-Migrate 4.0.5, Flask-SQLAlchemy 3.1.1, soundfile 0.12.1 (+12 more)

### Community 7 - "Frontend Dev Dependencies"
Cohesion: 0.11
Nodes (19): ajv, ajv-keywords, autoprefixer, devDependencies, ajv, ajv-keywords, autoprefixer, postcss (+11 more)

### Community 8 - "Voice Routes & TTS"
Cohesion: 0.19
Nodes (15): get_greeting(), google_callback(), process_voice(), get, jwt_required, post, Returns the audio for the initial greeting., _get_client() (+7 more)

### Community 9 - "Frontend Runtime Deps"
Cohesion: 0.12
Nodes (17): axios, date-fns, dependencies, axios, date-fns, jwt-decode, lucide-react, react (+9 more)

### Community 10 - "Auth & User Model"
Cohesion: 0.20
Nodes (11): User, current_user(), google_login(), login(), get, jwt_required, post, register() (+3 more)

### Community 11 - "External Integrations"
Cohesion: 0.15
Nodes (15): google-api-python-client 2.152.0, google-auth 2.23.4, google-auth-oauthlib 1.2.0, google-generativeai >=0.8.3, python-dotenv 1.0.1, /api/calendar/sync Endpoint, Calendar Sync Stub, Env-Var Service Plug-in Pattern (+7 more)

### Community 12 - "App Factory & Config"
Cohesion: 0.38
Nodes (7): Config, create_app(), Flask, register_extensions(), register_healthcheck(), Flask, register_blueprints()

### Community 13 - "Architecture Overview"
Cohesion: 0.25
Nodes (9): Flask REST API Backend, PostgreSQL/SQLite Database, React SPA Frontend, SmartMeet AI Architecture Document, React App Shell (index.html), #root Mount Point, Flask Backend API, React Frontend (Tailwind UI) (+1 more)

### Community 14 - "DB Migrations Env"
Cohesion: 0.39
Nodes (7): get_engine(), get_engine_url(), get_metadata(), Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online()

### Community 15 - "PWA Manifest"
Cohesion: 0.25
Nodes (7): background_color, display, icons, name, short_name, start_url, theme_color

### Community 16 - "Voice Command Parsing"
Cohesion: 0.52
Nodes (6): _extract_datetime(), _extract_duration(), _extract_title(), parse_voice_command(), datetime, VoiceCommand

## Ambiguous Edges - Review These
- `OpenAI Integration Hook` → `google-generativeai >=0.8.3`  [AMBIGUOUS]
  README.md · relation: references

## Knowledge Gaps
- **59 isolated node(s):** `name`, `version`, `private`, `description`, `author` (+54 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `OpenAI Integration Hook` and `google-generativeai >=0.8.3`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `VoiceCommandProcessor` connect `Command Processor Rationale` to `Voice Routes & TTS`, `NLP Parsing Services`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `User` connect `Auth & User Model` to `Data Models & Calendar Routes`, `NLP Parsing Services`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `create_event_from_conversation()` connect `NLP Parsing Services` to `Command Processor Rationale`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **What connects `name`, `version`, `private` to the rest of the system?**
  _59 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Data Models & Calendar Routes` be split into smaller, more focused modules?**
  _Cohesion score 0.07568027210884354 - nodes in this community are weakly interconnected._
- **Should `Command Processor Rationale` be split into smaller, more focused modules?**
  _Cohesion score 0.07084785133565621 - nodes in this community are weakly interconnected._