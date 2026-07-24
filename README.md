*This project has been created as part of the 42 curriculum by jili, wding, \<login3\>, \<login4\>, \<login5\>.*

# Chat 42 (Moulinette)

## Description

**Chat 42** is a campus-cat-sighting map built for 42's `ft_transcendence` project. Students photograph cats they
spot around campus, tag the sighting with a map zone, and the app builds a shared, real-time picture of where
campus cats hang out — their activity map, history, and patterns over time. An AI-driven persona, **Moulinette**
("the cat" in French), writes in-character diary entries and answers questions based on the real, crowdsourced
sighting data, and a "guess where the cat is" game turns the whole thing into a light competitive loop.

Key features (see [Features List](#features-list) and [Modules](#modules) for what's actually built vs. planned):

- Photo upload + map-zone tagging for cat sightings, filtered by an automated (zero-shot) cat detector
- A 2D campus map showing sighting activity, history, and per-cat profiles
- Moulinette's AI persona: auto-generated diary entries and natural-language Q&A grounded in real sighting data
- Standard account system (email/password) plus 42 OAuth login
- Friends, notifications, gamification (achievements, leaderboard, sighting-prediction game)
- Real-time updates over WebSocket when new sightings come in

<!-- TODO: once F2/F4/F5/F7/F8/F9/F10 land, expand this list to match what's actually shipped. -->

## Team Information

<!-- TODO: fill in real 42 logins, names, and confirm final role assignments. -->

| Login | Role(s) | Responsibilities |
|---|---|---|
| jili | Tech Lead, Backend Dev | Owns **F1** (platform: FastAPI/React scaffolding, auth — email/password + 42 OAuth, Docker deploy, Nginx/HTTPS, PP/ToS) and **F8** (search & analytics dashboard) |
| wding | AI Dev | Owns **F9** (Moulinette AI persona: diary generation, Q&A) and the cat-detection half of **F2** |
| \<login\> | PO, Design, Frontend Dev | Owns **F4** (map & cat profile pages, design system) |
| \<login\> | Frontend Dev | Owns **F2** (upload flow, PWA) and **F7** (gamification, friends) |
| \<login\> | PM, Fullstack Dev | Owns **F5** (WebSocket, notifications) and the remainder of **F8** (search, admin dashboard) |

## Project Management

<!-- TODO: fill in actual practices once the team settles on them. -->

- Task tracking: \<GitHub Issues / Trello / other\>
- Communication: \<Discord / Slack / other\>
- Meeting cadence: \<weekly / bi-weekly, etc.\>
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

Currently one table (more will be added as F2/F4/F5/F7/F8/F10 land — this section should be kept in sync):

**`users`**

| Column | Type | Notes |
|---|---|---|
| `id` | integer, PK | |
| `email` | varchar(255), unique, not null | Login identifier for both auth methods |
| `password_hash` | varchar(255), nullable | bcrypt hash; `null` for accounts created purely via 42 OAuth |
| `ft_login` | varchar(255), unique, nullable | 42 username; set when the account is linked to/created via 42 OAuth |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz | |

<!-- TODO: add sightings, zones, friendships, etc. tables here as they're built, plus a schema diagram. -->

## Features List

*Only features that are actually implemented and testable today. Update this as more branches land.*

| Feature | Description | Implemented by |
|---|---|---|
| Email/password signup & login | Account creation and login with bcrypt-hashed passwords, session via JWT cookie | \<your-login\> (F1) |
| 42 OAuth login | "Continue with 42" — authorizes via 42, auto-links to an existing account by email or creates a new one | \<your-login\> (F1) |
| Session persistence & logout | `GET /auth/me` restores login state on page load; logout clears the session cookie | \<your-login\> (F1) |
| Protected routes | Unauthenticated users are redirected to `/login` | \<your-login\> (F1) |
| Privacy Policy & Terms of Service pages | Project-specific content, linked from a site-wide footer | \<your-login\> (F1) |
| HTTPS everywhere | All external traffic terminated at Nginx with TLS; direct HTTP access to frontend/backend containers is not possible | \<your-login\> (F1) |

## Modules

Target: 14 mandatory points + up to 5 bonus points (19 total). Status reflects what's actually implemented, not just planned.

### Core (14 pts)

| Module | Type | Pts | Status | Branch |
|---|---|---|---|---|
| Web framework (React + FastAPI) | Major | 2 | ✅ Done | F1 |
| Real-time features (WebSocket) | Major | 2 | ⬜ Not started | F5 |
| Standard user management | Major | 2 | 🟡 Partial (auth done; profile/avatar/friends pending) | F1/F7 |
| Advanced permissions | Major | 2 | ⬜ Not started | F10 |
| Advanced analytics dashboard | Major | 2 | ⬜ Not started | F8 |
| ORM (SQLAlchemy) | Minor | 1 | ✅ Done | F1 |
| Advanced search | Minor | 1 | ⬜ Not started | F8 |
| OAuth 2.0 (42) | Minor | 1 | ✅ Done | F1 |
| PWA | Minor | 1 | ⬜ Not started | F2 |

### Differentiation (5 pts, plus 1 pt buffer)

| Module | Type | Pts | Status | Branch |
|---|---|---|---|---|
| LLM system interface (Moulinette persona) | Major | 2 | ⬜ Not started | F9 |
| File upload | Minor | 1 | ⬜ Not started | F2 |
| Image recognition (zero-shot cat detection) | Minor | 1 | ⬜ Not started | F2 |
| Gamification | Minor | 1 | ⬜ Not started | F7 |
| Notification system *(buffer, only if needed)* | Minor | 1 | ⬜ Not started | F5 |

<!-- TODO: as each module is finished, add its implementation description + justification here, especially for anything that ends up being a custom "Modules of choice" entry. -->

## Individual Contributions

<!-- TODO: every member fills in their own section as they contribute. -->

**jili** — F1 (Platform) & F8 (Search & Analytics)
- Backend/frontend scaffolding (FastAPI + React/Vite/Tailwind), Docker Compose setup with non-root containers.
- Email/password authentication (bcrypt, JWT-in-cookie) and 42 OAuth 2.0 login, including account auto-linking by email.
- PostgreSQL + SQLAlchemy async + Alembic migrations.
- Nginx reverse proxy with self-signed HTTPS, routing all traffic through a single origin.
- Privacy Policy / Terms of Service pages and site-wide footer.
- F8 (search, analytics dashboard): not started yet.

**\<login\> ("钩钩")** — F9 & F2 (cat detection) — *not started yet*

**\<login\>** — F4 — *not started yet*

**\<login\>** — F2 & F7 — *not started yet*

**\<login\>** — F5 & F8 (remainder) — *not started yet*

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

<!-- TODO: add real references as each branch is built (papers, library docs, tutorials actually used). -->

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 async ORM guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [42 API / OAuth documentation](https://api.intra.42.fr/apidoc)
- [Vite documentation](https://vite.dev/)


<!-- TODO: other members should add their own AI-usage disclosure here as they contribute to their branches. -->
