# Stock Financial Analysis Platform

Institutional-grade financial analysis platform — Bloomberg-style common-size financial statements, real-time stock streaming, and advanced analytics.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Browser                                            │
│  Next.js 15 (React, TypeScript, TanStack Query,     │
│              Zustand, Recharts, WebSocket)          │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS / WSS
┌──────────────────▼──────────────────────────────────┐
│  Nginx (reverse proxy, TLS, rate limiting)          │
└───────┬──────────────────────────┬──────────────────┘
        │ /api/v1/*                │ /*
┌───────▼──────────┐    ┌──────────▼──────────────────┐
│ FastAPI (Python) │    │ Next.js (Node.js SSR/SSG)   │
│ Uvicorn/Gunicorn │    └─────────────────────────────┘
└───────┬──────────┘
        │
┌───────▼──────────────────────────────────────────┐
│  PostgreSQL 16     Redis 7                       │
│  (financial data)  (cache + Celery broker)       │
└──────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────┐
│  Celery Worker + Beat                            │
│  (background data refresh — 27 hot tickers)      │
└──────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────┐
│  Financial Modeling Prep API (FMP)               │
│  (market data source — server-side only)         │
└──────────────────────────────────────────────────┘
```

## Features

- **Institutional financial statements** — Income Statement, Balance Sheet, Cash Flow with **common-size percentages** (% of revenue / total assets / OCF) and YoY growth, just like Bloomberg Terminal
- **Real-time price streaming** via WebSocket (15-second updates)
- **Analytics engine** — margins, ROE/ROA/ROIC, liquidity, leverage, valuation, FCF ratios
- **Auth** — Argon2 hashing, JWT with refresh-token rotation, RBAC, brute-force lockout
- **Caching** — Redis multi-tier (quotes 15s, financials 24h, analytics 4h)
- **Security** — OWASP-compliant headers, CSRF protection, rate limiting, input validation at all boundaries
- **Dark/light theme** — Bloomberg-inspired dark terminal by default

## Quick Start

### Prerequisites

- Docker & Docker Compose v2
- FMP API key (free at [financialmodelingprep.com](https://financialmodelingprep.com))

### 1. Clone & configure

```bash
git clone <repo-url>
cd stock_financial_analysis_platform

cp .env.example .env
# Edit .env — fill in all <REQUIRED> values
```

### 2. Generate secrets

```bash
# SECRET_KEY
openssl rand -hex 32

# JWT_SECRET_KEY
openssl rand -hex 32
```

### 3. Run database migrations

```bash
docker compose --profile migrate up migrate
```

### 4. Start all services

```bash
docker compose up -d
```

Open [http://localhost](http://localhost).

### Development mode (hot reload)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── analytics/          # Pure analytics engine (common_size, ratios)
│   │   ├── api/v1/             # FastAPI routers
│   │   ├── core/               # Config, DB, Redis, security, exceptions
│   │   ├── middleware/         # Security headers, structured logging
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic v2 schemas
│   │   ├── services/           # Business logic (auth, financials, FMP client)
│   │   └── tasks/              # Celery tasks
│   ├── alembic/                # Database migrations
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js 15 App Router pages
│   │   ├── components/         # React components
│   │   ├── hooks/              # TanStack Query + WebSocket hooks
│   │   ├── lib/                # Axios client, utilities
│   │   ├── store/              # Zustand stores
│   │   ├── types/              # TypeScript types
│   │   └── utils/              # Number formatters
│   └── Dockerfile
├── docker/
│   └── nginx/nginx.conf
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
└── .github/workflows/ci.yml
```

## Common-Size Financial Statements

Every financial statement row includes both the raw dollar value (in millions) and its structural percentage:

| Item | FY2023 | FY2022 | FY2021 |
|---|---|---|---|
| Revenue | 394,328 | 365,817 | 274,515 |
| Gross Profit | 169,148 (**42.9%**) | 152,836 (**41.8%**) | 104,956 (**38.2%**) |
| Operating Income | 114,301 (**29.0%**) | 119,437 (**32.6%**) | 108,949 (**39.7%**) |
| Net Income | 96,995 (**24.6%**) | 99,803 (**27.3%**) | 94,680 (**34.5%**) |

Toggle between `$ Millions` and `% Structure` views on every table.

## API Reference

Base URL: `/api/v1`

| Endpoint | Description |
|---|---|
| `POST /auth/register` | Create account |
| `POST /auth/login` | Obtain JWT tokens |
| `GET /stocks/search?q=AAPL` | Search stocks |
| `GET /stocks/{ticker}` | Profile + live quote |
| `GET /financials/{ticker}/income-statement` | Income statement with cs_* |
| `GET /financials/{ticker}/balance-sheet` | Balance sheet with cs_* |
| `GET /financials/{ticker}/cash-flow` | Cash flow with cs_* |
| `GET /financials/{ticker}/ratios` | Financial ratios |
| `WS /ws/stocks/{ticker}` | Live price stream |
| `GET /health` | Health check |

## Production Deployment

```bash
# Use production overrides (no source mounts, optimised resources)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Place SSL certs in:
#   docker/nginx/ssl/fullchain.pem
#   docker/nginx/ssl/privkey.pem
```

## Security

- Passwords hashed with **Argon2id** (time=2, memory=64MB)
- Refresh tokens stored as **SHA-256 hashes** in DB — raw token never persisted
- **Generic error messages** prevent user enumeration
- **Brute-force lockout**: 5 failed attempts → 15-minute lockout
- FMP API key **never logged** or exposed to browser
- All security headers per OWASP (CSP, HSTS, X-Frame-Options: DENY, etc.)
- Rate limiting: 60 req/min globally, 10 req/min on auth endpoints

## License

Private — all rights reserved.
