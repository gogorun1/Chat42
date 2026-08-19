*This project has been created as part of the 42 curriculum by jili, wding, slou, shazhu, lshenghu.*

# Chat 42 (Moulinette)

## Description

**Chat 42** is a campus-cat-sighting map built for 42's `ft_transcendence` project. Students photograph cats they
spot around campus, tag the sighting with a map zone, and the app builds a shared, real-time picture of where
campus cats hang out — their activity map, history, and patterns over time. An AI-driven persona, **Moulinette**, writes in-character diary entries and answers questions based on the real, crowdsourced
sighting data, and a "guess where the cat is" game turns the whole thing into a light competitive loop.

Key features (see [Features List](#features-list) and [Modules](#modules) for what's actually built vs. planned):

- Photo upload + map-zone tagging for cat sightings, filtered by an automated (zero-shot) cat detector
- A 2D campus map showing sighting activity
- Moulinette's AI persona: auto-generated diary entries and natural-language Q&A grounded in real sighting data
- Standard account system (email/password) plus 42 OAuth login
- Friends, notifications, gamification (achievements, leaderboard, sighting-prediction game)
- Real-time updates over WebSocket when new sightings come in


## Team Information

| Login | Role(s) | Responsibilities |
|---|---|---|
| jili | Tech Lead, Backend Dev | Owns **F1** (platform: FastAPI/React scaffolding, auth — email/password  + 42 OAuth, Docker deploy, Nginx/HTTPS, PP/ToS), **F7** (gamification, friends)  and **F10**   |
| wding | PM, AI Dev | Owns **F9** (Moulinette AI persona: diary generation, Q&A) and the cat-detection half of **F2** |
| slou | PO, Design, Frontend Dev | Owns **F4** (map, design system) |
| lshenghu | Frontend Dev | Owns **F2** (upload flow, PWA) |
| shazhu |  Fullstack Dev | Owns **F5** (WebSocket, notifications) and **F8** (search, admin dashboard) |

## Project Management

- Task tracking: \<GitHub Issues, Wechat\>
- Communication: \<Wechat, Google meeting\>
- Meeting cadence: \<Weekly group meetings, with additional meetings between 2–3 group members as needed.\>
- Branch strategy: one feature branch per roadmap item (F1, F2, F4, F5, F7, F8, F9, F10), reviewed before merge to `main`.

## Technical Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite + TypeScript, Tailwind CSS v4 | FastAPI is already the backend framework, so a full-stack framework like Next.js would mean two competing backends for no scoring benefit; Vite gives a fast, simple SPA setup. |
| Backend | FastAPI (async) | Native `async`/`await` and first-class WebSocket support, both needed for the realtime sighting broadcast module. |
| ORM / migrations | SQLAlchemy 2.0 (async) + Alembic | More flexible for the complex filtering/sorting/pagination queries planned for the search module than lighter alternatives (e.g. SQLModel). |
| Database | PostgreSQL 16 | Relational data (users, sightings, zones, friendships) with real foreign-key relationships; mature, well-supported by SQLAlchemy/Alembic. |
| Auth | Email/password (bcrypt-hashed, salted) + 42 OAuth 2.0, JWT in an `httpOnly`/`Secure`/`SameSite=Strict` cookie | Cookie-based sessions avoid exposing the token to JS (XSS resistance); OAuth accounts are auto-linked to an existing email/password account by 42-verified email, since 42 already verifies that email ownership. |
| Reverse proxy / TLS | Nginx, self-signed cert generated on first boot | Terminates HTTPS for all external traffic (mandatory requirement) and routes to the frontend/backend containers, which talk to each other over plain HTTP inside the Docker network (explicitly allowed by the subject). |
| Deployment | Docker Compose, single command | `frontend`, `backend`, `postgres`, `nginx` services; non-root container users (UID/GID configurable via `.env`) so bind-mounted dev files stay owned by the host user. |

## Database Schema

**users**

| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| email | varchar(255), unique, indexed, not null | Login identifier for both auth methods |
| password_hash | varchar(255), nullable | bcrypt hash; null for accounts created purely via 42 OAuth |
| ft_login | varchar(255), unique, indexed, nullable | 42 username; set when the account is linked to/created via 42 OAuth |
| role | enum `user_role` (`user`, `moderator`, `admin`), not null, default `user` | Drives F10 permission checks, also read by F8's moderation controls on the search page |
| display_name | varchar(50), nullable | Falls back to `email.split("@")[0]` in the UI until set |
| avatar_path | varchar(255), nullable | Served as `/uploads/{avatar_path}` via the `avatar_url` property |
| guess_points | integer, not null, default 5 | Spent/earned by F4's guessing game |
| created_at | timestamptz, server default now() | |
| updated_at | timestamptz, server default now(), updates on change | |

**zones**

| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| slug | varchar(64), unique, indexed, not null | Stable identifier used by the frontend map (e.g. `cantine_0`) |
| name | varchar(128), not null | Display name (e.g. "Shokudo") |

**sightings**

| Column | Type | Notes |
|---|---|---|
| id | integer, PK | |
| user_id | integer, FK → users.id, indexed, not null | Reporter |
| zone_id | integer, FK → zones.id, indexed, not null | |
| image_path | varchar(512), not null | Stored upload path; served as `/uploads/{image_path}` |
| created_at | timestamptz, server default now() | Sort key for F8's search, and for F5's real-time "new sighting" ordering |

**notifications**

| Column | Type | Notes |
|---|---|---|
| id | UUID, PK, default `uuid4()` | |
| user_id | integer, FK → users.id `ON DELETE CASCADE`, indexed, not null | Recipient |
| type | enum `notification_type` (`sighting_nearby`, `sighting_approved`, `sighting_rejected`, `sighting_removed`, `guess_result`, `badge_earned`, `friend_request`, `role_changed`, `system`), not null | Drives which icon/copy renders in the notification bell |
| title | varchar(140), not null | Human-readable message, e.g. "You earned a new badge!" |
| body | text, nullable | Optional longer detail |
| data | JSONB, not null, default `{}` | Structured payload (e.g. which sighting/zone triggered it) for the frontend to act on |
| read_at | timestamptz, nullable | Null = unread; `is_read` property derived from whether this is set |
| created_at | timestamptz, server default now() | |


## Features List

*Only features that are actually implemented and testable today. Update this as more branches land.*

| Feature | Description | Implemented by |
|---|---|---|
| Email/password signup & login | Account creation and login with bcrypt-hashed passwords, session via JWT cookie | jili (F1) |
| 42 OAuth login | "Continue with 42" — authorizes via 42, auto-links to an existing account by email or creates a new one | jili (F1) |
| Session persistence & logout | `GET /auth/me` restores login state on page load; logout clears the session cookie | jili (F1) |
| Cat sighting upload | Photo upload with map-zone tagging, validated through cat-detection pipeline | lshenghu (F2 upload flow); wding (F2 cat-detection pipeline) |
| PWA install | Installable web app with offline app shell via service worker | lshenghu (F2) |
| Protected routes | Unauthenticated users are redirected to `/login` | jili (F1) |
| Privacy Policy & Terms of Service pages | Project-specific content, linked from a site-wide footer | jili (F1) |
| HTTPS everywhere | All external traffic terminated at Nginx with TLS; direct HTTP access to frontend/backend containers is not possible | jili (F1) |
| Interactive campus map UI| SVG-based campus map with zone selection, and structured TypeScript zone data used to associate sightings with their location| slou(F4)|
| Website UI & responsive design | React/TypeScript frontend with Tailwind, responsive layouts, reusable UI components, forms, navigation, buttons, and vintage game styling and animations.| slou(F4)|
| Real-time notifications (WebSocket) | Instant, push-based delivery — no polling — for badge-earned, role-change, and sighting-deletion events, surfaced via a live notification bell | shazhu (F5) |
| Advanced sighting search | `/api/search/sightings` — filter by zone and date range, sort by creation date or zone, paginated results; all filters strictly typed so malformed input is rejected before it reaches the database | shazhu (F8) |
| Analytics dashboard | Admin-only charts over sighting history, gated behind the F10 role check, including an all-time top-reporters view independent of the currently selected date/zone filters, with CSV/PDF export | shazhu (F8) |
| Role-based moderation on search results | Moderators/admins can remove a sighting directly from the search page, triggering the F5 deletion notification to the original reporter | shazhu (F5 + F8, integrating with jili F10's role system) |
| Moulinette AI diary & Q&A | Daily auto-generated diary entry (cached per day) and streaming natural-language Q&A over SSE, both grounded in the day's real sighting data, with rate limiting | wding (F9) |
| Gamification | Milestone/streak badges, a combined leaderboard (sightings + guess points), and a "guess the current zone" points game | jili + shazhu (F7) |

## Modules

Target: 14 mandatory points + up to 5 bonus points (19 total). Status reflects what's actually implemented, not just planned.

### Core (14 pts)

| Module | Type | Pts | Status | Branch |
|---|---|---|---|---|
| Web framework (React + FastAPI) | Major | 2 | ✅ Done | F1 |
| Real-time features (WebSocket) | Major | 2 | ✅ Done | F5 |
| Standard user management | Major | 2 | 🟡 Partial — profile/avatar/friends done; **online status not yet implemented** (`websocket_manager.py` has no presence tracking) | F1/F7 |
| Advanced permissions | Major | 2 | ✅ Done | F10 |
| Advanced analytics dashboard | Major | 2 | ✅ Done — charts + CSV/PDF export (`lib/exportHelpers.ts`) | F8 |
| ORM (SQLAlchemy) | Minor | 1 | ✅ Done | F1 |
| Advanced search | Minor | 1 | ✅ Done | F8 |
| OAuth 2.0 (42) | Minor | 1 | ✅ Done | F1 |
| PWA | Minor | 1 | ✅ Done — `vite-plugin-pwa` with manifest + workbox runtime caching (`vite.config.ts`); verify install on a real device before the defense | F2 |

### Differentiation (5 pts, plus 1 pt buffer)

| Module | Type | Pts | Status | Branch |
|---|---|---|---|---|
| LLM system interface (Moulinette persona) | Major | 2 | ✅ Done — Gemini client with streaming, diary generation + Q&A over SSE, rate limiting (`routers/ai.py`, `services/gemini_llm_client.py`, `services/question_service.py`) | F9 |
| File upload | Minor | 1 | ✅ Done | F2 |
| Image recognition (zero-shot cat detection) | Minor | 1 | ✅ Done — real HuggingFace `zero-shot-object-detection` pipeline, wired into the sighting-upload flow (`services/cat_detector_factory.py`, `routers/sightings.py`); the "tagging" half of the module description is thin (binary cat/not-cat only) — worth a note in the demo | F2 |
| Gamification | Minor | 1 | ✅ Done — badge rules, leaderboard, guess-the-zone points game (`services/gamification_service.py`, `routers/gamification.py`) | F7 |
| Notification system *(buffer, only if needed)* | Minor | 1 | ✅ Done | F5 |

<!-- TODO: as each module is finished, add its implementation description + justification here, especially for anything that ends up being a custom "Modules of choice" entry. -->

> Status verified against the actual code on 2026-08-19 (not just branch/PR titles). Core + differentiation total to 19/19 at the code level; the one open gap is online status for the Standard user management module.

## Individual Contributions

**jili** — F1 (Platform) & F7 & F10
- Backend/frontend scaffolding (FastAPI + React/Vite/Tailwind), Docker Compose setup with non-root containers.
- Email/password authentication (bcrypt, JWT-in-cookie) and 42 OAuth 2.0 login, including account auto-linking by email.
- PostgreSQL + SQLAlchemy async + Alembic migrations.
- Nginx reverse proxy with self-signed HTTPS, routing all traffic through a single origin.
- Privacy Policy / Terms of Service pages and site-wide footer.
- Advanced permissions (F10): user/moderator/admin roles, role-gated views and actions.
- Gamification backend (F7): badge rules and award logic, leaderboard endpoint, guess-the-zone points game (with **shazhu**, who wired badge-earned events into the F5 notification pipeline).

**wding** — F9 & F2 (cat detection)
- Moulinette AI persona (F9): grounded diary generation and Q&A using aggregated sighting data, a Gemini-backed LLM interface, PostgreSQL daily caching, SSE streaming, and per-user rate limiting.
- Zero-shot cat detection (F2): configurable HuggingFace `zero-shot-object-detection` pipeline integrated into the upload flow to reject non-cat photos before storage.

**slou** — F4
- Designed the core game concept and gameplay loop around finding Moulinette on the 42 campus.
- Defined the guessing point system: spending 1 point to guess and earning 3 points for a correct guess.
- Defined the user experience for guess, skip, results, history, heat map, diary, and ranking features.
- Coordinated the product vision between the frontend and backend, ensuring that the implemented features match the intended gameplay experience.
- React/Vite/Tailwind frontend scaffolding with a game-style Chat42 UI and game navigation through a reusable `GameMenu`.
- Campus map with selectable zones, Moulinette display, and the UI of last-sighting information, history, heat map, diary, and ranking views.
- Moulinette intro/guess flow: users can choose to guess her location for 1 point, earn 3 points for a correct guess, or skip and directly view the last-sighting.
- Cat sighting report UI (upload function realised by **lshenghu** - **F2**).

**lshenghu** — F2
- Cat sighting upload flow: photo capture/selection, preview, and map-zone tagging before submission.
- PWA shell: web app manifest, service worker, and offline app-shell caching via `vite-plugin-pwa`.

**shazhu** — F5 & F8 
- Real-time notification system over WebSocket: badge-earned, role-change, and sighting-deletion notifications are pushed to the client the instant they happen — via a notify_user() service on the backend and a live NotificationBell component on the frontend — rather than the client having to poll for updates.
- Advanced sighting search (/api/search/sightings): filter by zone and date range, sortable by creation date or zone, paginated results. All filters are strictly typed (Pydantic int/datetime), so malformed input is rejected with a 422 before it ever reaches the database — verified directly with manual SQL-injection-style test payloads.
- Analytics dashboard: admin-only, gated behind the F10 role check, including a top-reporters view that intentionally stays all-time regardless of whichever date/zone filters are selected elsewhere on the page.
- Role-based moderation integrated into search: moderators/admins can remove a sighting directly from the search results, which triggers the F5 deletion notification to the original reporter — connecting F5, F8, and F10's role system.


## Instructions

### Prerequisites

- Docker + Docker Compose (v2, i.e. the `docker compose` command, not the legacy `docker-compose`)
- A 42 intra account, to register an OAuth application (needed for "Continue with 42" to work)

### Setup

1. Copy the environment template and fill it in:
   ```sh
   cp .env.example .env
   ```
   - `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`: pick any values for local dev.
   - `HOST_UID` / `HOST_GID`: run `id -u` and `id -g` on your machine and put the results here — keeps files
     that containers create on your bind-mounted source tree owned by you instead of root.
   - `JWT_SECRET_KEY`: generate one with:
     ```sh
     python3 -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - `FT_CLIENT_ID` / `FT_CLIENT_SECRET`: register an application at
     https://profile.intra.42.fr/oauth/applications/new — type "42 Pedagogical Project", scope "Access the user
     public data" only, **not** marked Public, Redirect URI set to `https://localhost/auth/42/callback`. Copy
     the UID/Secret it gives you into `.env`.
   - `FT_REDIRECT_URI`: leave as `https://localhost/auth/42/callback` (must exactly match what you registered above).

2. Run everything with a single command:
   ```sh
   docker compose up -d --build
   ```
   This starts `postgres`, `backend`, `frontend`, and `nginx`. On first boot, `nginx` generates a self-signed TLS
   certificate automatically (persisted in a volume, so this only happens once).

3. Apply database migrations (first run only, or after pulling new migrations):
   ```sh
   docker compose exec backend alembic upgrade head
   ```

4. Open **https://localhost** in Chrome. You'll get a "connection isn't private" warning the first time — that's
   expected for a self-signed dev certificate, not a bug; click "Advanced" → "Proceed to localhost".

### Useful commands

```sh
docker compose logs -f <service>              # tail logs for frontend/backend/nginx/postgres
docker compose exec backend alembic revision --autogenerate -m "message"   # new migration
docker compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB        # DB shell
```

See [`docs/API.md`](docs/API.md) for how auth works end to end and conventions for adding new backend routes.
The backend's interactive API reference is available at https://localhost/docs while the stack is running.

## Resources

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 async ORM guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [42 API / OAuth documentation](https://api.intra.42.fr/apidoc)
- [Vite documentation](https://vite.dev/)


<!-- TODO: other members should add their own AI-usage disclosure here as they contribute to their branches. -->
## AI-usage
| Login | Part | AI-usage |
|---|---|---|
| jili | F1, F7, F10 | Used to help debug issues during development (Docker/Nginx setup, Alembic migrations, auth/permissions logic). |
| wding | F2, F9 | |
| slou | F4 |AI is used to transform real photos of the school and cat into a painting style.  |
| lshenghu | F2 | Used to help implement and debug frontend/backend integration during development. |
| shazhu | F5, F8 | Used to help review WebSocket/notification architecture and role-based moderation logic, debug an Nginx trailing-slash redirect and an Alembic migration issue. |
