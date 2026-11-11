# 01 — Requirements

## 1. Problem

Residents of Uzbek cities lack an easy way to (a) see air quality near them and (b) report local environmental problems to people who can act on them. There is also little incentive to take part in environmental activity.

## 2. Goal of the MVP

A working Android app + API that lets a citizen **check air quality**, **report a problem with photo and location**, and **earn points when the report is verified** — deployed and usable by real people in Tashkent.

## 3. User roles

| Role | Who | Can do |
|---|---|---|
| **Guest** | Not logged in | View the map, air quality, public (verified) reports, leaderboards |
| **Citizen** | Registered user | Everything a Guest can + create reports, see own reports and points |
| **Moderator** | Trusted staff/volunteer | Verify / reject reports, change report status (via Django Admin) |
| **Admin** | Project owner | Everything + manage users, categories, eco-points, districts |

## 4. Functional requirements

IDs are referenced later in code, tests and commits (e.g. `feat(reports): duplicate detection [FR-R5]`).

### 4.1 Authentication & profile (A)

| ID | Requirement |
|---|---|
| FR-A1 | User registers with email + password (+ display name, district). |
| FR-A2 | User logs in and receives an access token (short-lived) and a refresh token. |
| FR-A3 | App silently refreshes the access token using the refresh token. |
| FR-A4 | Logout invalidates the refresh token on the server (blacklist). |
| FR-A5 | User can view and edit their profile (display name, district, avatar). |

### 4.2 Air quality (AQ)

| ID | Requirement |
|---|---|
| FR-AQ1 | System fetches readings from an external air-quality API **every hour** (background job). |
| FR-AQ2 | List of monitoring stations with their latest reading (AQI + pollutants). |
| FR-AQ3 | Return the **nearest station** to a given location. |
| FR-AQ4 | History for a station: last 24 h and last 7 days (for charts). |
| FR-AQ5 | Each AQI value has a category (Good … Hazardous), a colour and health advice, including advice for sensitive groups (children, elderly, respiratory conditions). |

### 4.3 Reports (R)

| ID | Requirement |
|---|---|
| FR-R1 | Citizen creates a report: **1–3 photos**, category, description (≤ 500 chars), location (lat/lng). |
| FR-R2 | Map endpoint returns reports inside a **bounding box** (the visible map area), filterable by category and status. |
| FR-R3 | Report detail: photos, category, description, status, status history, created date. Reporter shown by display name only. |
| FR-R4 | Citizen sees a list of their own reports with statuses. |
| FR-R5 | **Duplicate detection:** a new report within **50 m** of an open report of the same category (created in the last 30 days) is linked to it instead of creating a separate map point. |
| FR-R6 | Status workflow: `new → verified → in_progress → resolved`, or `new → rejected` (with reason). |
| FR-R7 | Citizen can delete their own report **only while it is `new`**. |
| FR-R8 | Guests and other citizens see only `verified`, `in_progress`, `resolved` reports — never `new` or `rejected`. |

Categories (admin-managed): Illegal dump · Tree damage / cutting · Air pollution source (smoke, burning) · Water / irrigation problem · Other.

### 4.4 Moderation (M)

| ID | Requirement |
|---|---|
| FR-M1 | Moderators see a queue of `new` reports in Django Admin, oldest first, with photos and a map preview. |
| FR-M2 | Moderator verifies or rejects (reason required on reject). |
| FR-M3 | Every status change is stored in a status history (who, when, from, to, note). |

### 4.5 Eco Points & leaderboard (P)

| ID | Requirement |
|---|---|
| FR-P1 | +10 points when a report is **verified**; +5 bonus when it becomes **resolved**. Points are never given at creation time (anti-fraud). |
| FR-P2 | Points are stored as an **append-only ledger** (each change is a row with reason and source); rows are never edited or deleted. Corrections are new negative rows. |
| FR-P3 | User balance = sum of their ledger rows. |
| FR-P4 | Leaderboards: top users and top districts, for "this month" and "all time". |

### 4.6 Map layers (G)

| ID | Requirement |
|---|---|
| FR-G1 | Map shows three layers: 🔴 reports, 🟢 eco-points (recycling points, parks — admin-managed), 🔵 air monitoring stations. Each layer can be toggled. |

## 5. Non-functional requirements

| Area | Requirement |
|---|---|
| **Security** | OWASP Top 10 aware. Object-level permissions on every endpoint (no IDOR). Rate limiting on auth and report creation. Passwords hashed (Django default PBKDF2 / Argon2). Secrets only via environment variables. |
| **Image handling** | Max 5 MB per photo, JPEG/PNG/WebP only (checked by content, not extension), re-encoded server-side, resized to max 1600 px, **EXIF metadata stripped** (privacy). |
| **Privacy** | Reporter's email is never exposed in the API. Report location is the problem's location, not tracked continuously. |
| **Performance** | Map bbox endpoint p95 < 300 ms for up to 500 points (spatial index on geometry). |
| **Reliability** | If the external air API fails, the app shows the last known reading with its timestamp — never crashes or shows empty data silently. |
| **Language** | UI in Uzbek (Latin). Strings kept in translation files so Russian/English can be added later. |
| **Quality** | Backend test coverage ≥ 80 % for services and permissions. CI runs lint + tests on every push. |
| **Platform** | Android 8+ for MVP. Code stays cross-platform so iOS can be built later without rewrites. |

## 6. Out of scope for the MVP

Kept out deliberately so the MVP ships. Each can become a later stage.

- iOS build and App Store release
- Public web portal for citizens (moderators use Django Admin)
- IoT sensor ingestion (designed for: a future `/ingest` endpoint with per-device API keys)
- AI photo classification
- Partner vouchers / reward shop
- Blockchain (the append-only ledger provides the needed transparency)
- Push notifications (planned right after MVP for "air quality is bad today" alerts)

## 7. Key user stories with acceptance criteria

**US-1 — Report an illegal dump**
> As a citizen, I want to photograph an illegal dump and send it with my location, so that it gets cleaned up.

- Given I am logged in and granted camera + location permissions
- When I take 1–3 photos, choose "Illegal dump", optionally add text, and press Send
- Then the report is saved with status `new`, I see it under "My reports", and it is **not** yet visible to others
- And if an open "Illegal dump" report exists within 50 m, mine is linked to it and I'm told so

**US-2 — Check the air before going out**
> As a parent, I want to see the air quality near me, so that I can decide whether my child should play outside.

- When I open the app, I see the AQI of the nearest station, its category colour, last update time, and advice for children
- If the data is older than 3 hours, a "data may be outdated" notice is shown

**US-3 — Moderate a report**
> As a moderator, I want to verify or reject new reports quickly, so that the map stays trustworthy.

- I see `new` reports oldest first with photos and location
- Verifying makes it public and awards the reporter 10 points (exactly once, even if I click twice)
- Rejecting requires a reason; no points are awarded
