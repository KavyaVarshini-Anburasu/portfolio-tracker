<div align="center">

# 📈 Portfolio Tracker

A full-stack investment portfolio tracker built with **Django**, **Strawberry GraphQL**, **React**, and **Apollo Client**.

Track your holdings, log buy/sell transactions, and view real-time portfolio valuations — all through a clean, modern interface powered by a GraphQL API.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![GraphQL](https://img.shields.io/badge/GraphQL-Strawberry-E10098?logo=graphql&logoColor=white)](https://strawberry.rocks)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)](https://vite.dev)

</div>

---

## ✨ Features

- **Multi-portfolio support** — Organize investments across separate portfolios
- **Transaction ledger** — Record buy/sell transactions with full CRUD operations
- **Derived calculations** — Shares owned, holding value, and portfolio totals are computed server-side from the transaction history
- **Oversell protection** — Atomic database checks prevent selling more shares than you own
- **Session authentication** — Secure login/logout with Django sessions
- **GraphQL API** — Flexible queries and mutations via Strawberry GraphQL
- **Dark mode** — Automatic light/dark theme based on system preference

---

## 🏗️ Architecture

```
┌──────────────────────┐         GraphQL          ┌──────────────────────┐
│                      │  ◄───────────────────►   │                      │
│   React + Apollo     │    /graphql/ endpoint    │  Django + Strawberry  │
│   (Vite dev server)  │                          │  (Python backend)     │
│   :5173              │                          │  :8000                │
│                      │                          │                      │
└──────────────────────┘                          └──────────┬───────────┘
                                                             │
                                                             ▼
                                                  ┌──────────────────────┐
                                                  │     PostgreSQL       │
                                                  │     (database)       │
                                                  └──────────────────────┘
```

### Data Model

```
User ──< Portfolio ──< Holding ──< Transaction
```

- A **User** owns multiple **Portfolios**
- Each **Portfolio** contains multiple **Holdings** (identified by ticker)
- Each **Holding** has a list of **Transactions** (buy/sell)
- **Shares owned**, **holding value**, and **portfolio total** are all *derived* from the transaction ledger — never stored directly

---

## 🛠️ Tech Stack

| Layer      | Technology                                                                 |
| ---------- | -------------------------------------------------------------------------- |
| Frontend   | React 19, Apollo Client 4, Vite 8                                         |
| Backend    | Django 5.2, Strawberry GraphQL                                             |
| Database   | PostgreSQL                                                                 |
| API        | GraphQL (queries + mutations over a single `/graphql/` endpoint)           |
| Auth       | Django session-based authentication (login/logout via GraphQL mutations)   |
| Linting    | oxlint (frontend)                                                          |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **PostgreSQL** running locally

### 1. Clone the repository

```bash
git clone https://github.com/KavyaVarshini-Anburasu/portfolio-tracker.git
cd portfolio-tracker
```

### 2. Backend setup

```bash
# Create and activate a virtual environment
cd portfolio-tracker
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# Install dependencies
pip install django strawberry-graphql django-cors-headers psycopg2-binary

# Create the PostgreSQL database
createdb portfolio

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Start the backend server
python manage.py runserver
```

The GraphQL API will be available at **http://localhost:8000/graphql/** with an interactive GraphiQL explorer.

### 3. Frontend setup

```bash
# From the project root
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at **http://localhost:5173**.

---

## 📁 Project Structure

```
.
├── frontend/                    # React SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx        # Main authenticated view
│   │   │   ├── LoginForm.jsx        # Authentication form
│   │   │   ├── PortfolioList.jsx     # Portfolio overview with grand total
│   │   │   ├── PortfolioCard.jsx     # Individual portfolio display
│   │   │   ├── HoldingsTable.jsx     # Holdings within a portfolio
│   │   │   ├── AddTransactionForm.jsx # Buy/sell entry form
│   │   │   ├── TransactionHistory.jsx # Transaction log
│   │   │   └── TransactionRow.jsx    # Editable transaction row
│   │   ├── api.js               # GraphQL queries & mutations
│   │   ├── format.js            # Currency formatting utilities
│   │   ├── App.jsx              # Root component (auth gate)
│   │   └── main.jsx             # Apollo Client setup & entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── portfolio-tracker/           # Django backend
│   ├── config/
│   │   ├── settings.py          # Django configuration
│   │   ├── urls.py              # URL routing (/graphql/, /admin/)
│   │   └── wsgi.py
│   ├── portfolios/
│   │   ├── models.py            # Portfolio, Holding, Transaction models
│   │   ├── types.py             # Strawberry GraphQL type definitions
│   │   ├── schema.py            # GraphQL queries & mutations
│   │   └── migrations/
│   └── manage.py
│
├── .gitignore
└── README.md
```

---

## 📡 GraphQL API

### Queries

| Query        | Description                                      |
| ------------ | ------------------------------------------------ |
| `me`         | Returns the currently authenticated user, or null |
| `portfolios` | All portfolios for the logged-in user             |

### Mutations

| Mutation             | Description                          |
| -------------------- | ------------------------------------ |
| `login`              | Authenticate with username/password  |
| `logout`             | End the current session              |
| `addTransaction`     | Record a new buy/sell transaction    |
| `updateTransaction`  | Edit an existing transaction         |
| `deleteTransaction`  | Remove a transaction                 |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
