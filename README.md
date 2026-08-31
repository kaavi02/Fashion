# VOGUE FIT - Contemporary Luxury Fashion E-Commerce

A full-stack, enterprise-grade Fashion E-Commerce application engineered with **FastAPI**, **MySQL 8.x Relational Database**, **SQLAlchemy ORM**, **Alembic Migrations**, **JWT (OAuth2 + Bcrypt) Authentication**, a proprietary **AI Biometric Size Recommendation Engine**, and a modern, responsive **HTML5/Bootstrap 5** storefront.

---

## 🌟 Core Features & Implementation Highlights

| Feature | Description | Priority |
|---|---|---|
| **Product Catalog** | Fashion items with multi-size & color variations, categories, brands, high-res lifestyle imagery, and stock management. | **High** |
| **Product Filters** | Live filtering by category, brand, size, color swatch, price slider, and gender. Sorting by popular, price, newest. | **High** |
| **AI Size Advisor** | Biometric sizing engine that calculates optimal garment size, fit confidence %, and personalized tailored commentary based on user measurements. | **High** |
| **Shopping Cart** | Dynamic cart supporting both authenticated users & persistent guest sessions, quantity controls, stock limits, and shipping calculations. | **High** |
| **Checkout Process** | Multi-step streamlined checkout with address validation, delivery options, and payment selection (Card, UPI, NetBanking, COD). | **High** |
| **User Authentication** | JWT-based authentication (Register, Login, Profile, Saved Addresses) with Bcrypt password hashing. | **High** |
| **Order Management** | Order history with live visual tracking timelines (Confirmed -> Packed -> In Transit -> Delivered). | **Medium** |
| **Wishlist** | 1-click wishlist toggle with live counter and direct move-to-bag capabilities. | **Low** |
| **Stitch MCP Connectivity** | Verified and connected to Stitch MCP server. | **Verified** |

---

## 🗄️ Database & Environment Configuration

### MySQL 8.x Database (Aiven Cloud)
The system is configured with your Aiven Cloud MySQL credentials in `.env`:
```env
# Database Settings
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_database_host
DB_PORT=12853
DB_NAME=defaultdb
DB_SSL_MODE=REQUIRED

# SQLAlchemy Database URL
DATABASE_URL=mysql+pymysql://your_db_user:your_db_password@your_database_host:12853/defaultdb
```

> **Resilient Database Fallback**: If the cloud MySQL server is momentarily unreachable (e.g. DNS propagation or network policy), the system automatically falls back to an embedded SQLite database (`fashion_store.db`) so development and testing proceed uninterrupted. As soon as the MySQL instance is active, it seamlessly uses MySQL.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.8+ installed (Tested on Python 3.13)
- Git installed

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Launch the Application
Run the unified launcher script:
```bash
python run.py
```
This script automatically:
1. Connects to the database (MySQL with SQLite fallback).
2. Creates all tables and indexes.
3. Seeds the fashion catalog with categories, brands, products, variants, and test users.
4. Starts the FastAPI Uvicorn server on **http://127.0.0.1:8000**.

### 4. Access URLs
- **Web Storefront**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **System Health & DB Status**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 🔑 Pre-Configured Demo Credentials

For quick testing, you can use the instant one-click login buttons on the [Sign In Page](http://127.0.0.1:8000/login):

| Role | Email | Password | Pre-loaded Data |
|---|---|---|---|
| **Customer** | `demo@fashion.com` | `Password123!` | Pre-saved body biometrics (Height: 178cm, Chest: 99cm, Waist: 83cm) for instant AI sizing |
| **Store Admin** | `admin@fashion.com` | `Admin123!` | Administrative privileges |

---

## 🧠 AI Size Recommendation Engine

The AI Size Advisor (`backend/app/services/ai_size_engine.py`) takes:
- **Biometric Inputs**: Gender, Height (cm), Weight (kg), Chest (cm), Waist (cm), Hips (cm).
- **Style Preference**: Slim / Athletic, Regular, or Relaxed / Oversized.
- **Garment Category**: Calibrated specifically for tops, shirts, denim pants, trousers, or dresses.

It calculates ease tolerance, BMI classification, and multi-dimensional metric distances to predict:
1. **Optimal Size** (e.g. `M`, `L`, `32`, etc.).
2. **Confidence Percentage** (e.g. `96% Match`).
3. **Personalized Commentary** (e.g. *"Optimal proportion with natural drape and unrestricted movement across chest."*).
4. **Alternative Size Option** (e.g. *"Choose Size L if you prefer a modern oversized drape."*).

---

## 🛠️ Alembic Database Migrations

To generate and apply migrations:
```bash
# Generate a new migration revision
alembic revision --autogenerate -m "Initial tables"

# Upgrade database to latest revision
alembic upgrade head
```

---

## 📁 Architecture & File Layout

```
kavya2/
├── backend/
│   ├── alembic/              # Database migration scripts & environment
│   ├── app/
│   │   ├── api/              # REST API route controllers
│   │   │   ├── auth.py       # JWT Register, Login, Profile & Measurements
│   │   │   ├── products.py   # Catalog, multi-criteria filters & details
│   │   │   ├── cart.py       # Shopping bag & stock management
│   │   │   ├── orders.py     # Checkout authorization & order tracking
│   │   │   ├── wishlist.py   # Customer wishlist management
│   │   │   └── size_advisor.py # AI size recommendation endpoints
│   │   ├── core/
│   │   │   ├── config.py     # Application environment settings
│   │   │   ├── database.py   # SQLAlchemy engine & MySQL SSL setup
│   │   │   └── security.py   # Bcrypt hashing & JWT token encoding
│   │   ├── models/
│   │   │   └── models.py     # SQLAlchemy ORM relational models
│   │   ├── schemas/
│   │   │   └── schemas.py    # Pydantic schemas for data validation
│   │   ├── services/
│   │   │   ├── ai_size_engine.py # Biometric sizing prediction engine
│   │   │   └── seed_data.py  # Realistic fashion catalog seeder
│   │   └── main.py           # FastAPI application & template mounting
├── frontend/
│   ├── static/
│   │   ├── css/style.css     # Luxury fashion design system
│   │   └── js/               # Modular frontend scripts (API, Cart, AI Advisor)
│   └── templates/            # Jinja2 HTML5 responsive views
├── .env                      # Active environment configuration
├── .env.example              # Template environment configuration
├── alembic.ini               # Alembic configuration
├── requirements.txt          # Python dependencies
└── run.py                    # Server startup script
```
