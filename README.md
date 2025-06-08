# AI-Powered Outreach Application Backend

## Overview

This project is the backend for an AI-powered email outreach application, similar in concept to tools like Woodpecker.io and Instantly.io. It allows users to manage campaigns, import contacts via CSV, generate personalized email templates using Large Language Models (LLMs) based on user prompts, send emails (including automated follow-ups), and track email opens. The primary goal is to leverage AI to customize and personalize outreach efforts effectively.

## Tech Stack

### Backend
*   **Language:** Python 3.8+
*   **Framework:** FastAPI
*   **Database:** PostgreSQL
*   **ORM:** SQLAlchemy
*   **Authentication:** JWT (JSON Web Tokens) with Passlib for password hashing
*   **Scheduling:** APScheduler (for follow-ups and other background tasks)
*   **Email Sending:** SMTP (using `aiosmtplib`)
*   **AI Integration:** Designed for integration with LLMs like OpenAI's GPT series.
*   **Data Validation:** Pydantic

### Frontend (User's Choice)
*   **Framework:** Next.js (React) has been indicated as the preferred choice.

## Getting Started / Backend Setup

These instructions will guide you through setting up and running the backend server locally.

### Prerequisites
*   Python 3.8 or higher
*   PostgreSQL server installed and running
*   Access to an SMTP server (for sending emails)
*   An API key for an LLM provider (e.g., OpenAI) if using the AI email generation feature.

### 1. Clone the Repository
```bash
# git clone <repository_url> # Replace with your repo URL
# cd <repository_name>
```

### 2. Create a Virtual Environment
It's highly recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scriptsctivate
```

### 3. Install Dependencies
Install all required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root of the backend project (e.g., within the `src` directory or project root, depending on how `pydantic-settings` is configured - typically project root). This file will store your configuration secrets and settings.

**Important:** Add `.env` to your `.gitignore` file to prevent committing secrets.

Fill the `.env` file with the following (replace placeholder values with your actual settings):

```env
# Database Configuration
DATABASE_URL="postgresql://user:password@host:port/dbname"

# JWT Authentication
JWT_SECRET="YOUR_VERY_STRONG_RANDOM_JWT_SECRET_KEY" # Generate a strong secret key
# JWT_ALGORITHM="HS256" # Already set in code, but can be configurable
# ACCESS_TOKEN_EXPIRE_MINUTES=30 # Already set in code, but can be configurable

# OpenAI API Key (for LLM email generation)
OPENAI_API_KEY="sk-YOUR_OPENAI_API_KEY"

# SMTP Server Configuration (for sending emails)
SMTP_HOST="your.smtp.host.com"
SMTP_PORT=587 # Or 465 for SSL
SMTP_USER="your_smtp_username"
SMTP_PASSWORD="your_smtp_password"
SMTP_SENDER_EMAIL="your_sender_email@example.com" # Default 'From' address
SMTP_USE_TLS="true" # Or "false"

# Application Base URL (for tracking pixel URLs)
APP_BASE_URL="http://localhost:8000" # Change for development/production
```
*(Note: The application needs to be configured to load these from the `.env` file, typically using `pydantic-settings` in a `core/config.py` module.)*

### 5. Database Setup
The SQL schema files are located in the `database/schema/` directory. You need to execute these against your PostgreSQL database to create the necessary tables.
1.  Ensure your PostgreSQL server is running and you can connect to it.
2.  Create a new database for the application if you haven't already.
3.  Run the SQL files in order (e.g., `001_...sql`, `002_...sql`, etc.) using a PostgreSQL client like `psql` or a GUI tool.
    *   **Important:** Review `database/schema/005_create_sent_emails_table.sql` and ensure the `triggered_by_rule_id` field and its index are included, as this was a guided modification during development.

*(For a more robust setup, consider using a migration tool like Alembic, which can be configured based on the SQLAlchemy ORM models.)*

### 6. Running the FastAPI Application
Once the environment variables are set and the database is ready, you can run the FastAPI application using Uvicorn:
```bash
# Assuming your FastAPI app instance is in `src.main.app`
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
*   `--reload`: Enables auto-reload during development. Remove for production.
*   The application should now be accessible at `http://localhost:8000` (or your `APP_BASE_URL`).
*   API documentation will typically be available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

## API Endpoint Summary

The backend provides a comprehensive set of APIs for managing the outreach application:

*   **Authentication (`/auth`):** Signup, Login (JWT token-based).
*   **Users (`/users`):** Get and update current user's profile (name, role, company).
*   **Campaigns (`/campaigns`):** CRUD operations for campaigns, CSV contact upload, triggering campaign sending.
*   **LLM Email Generation (`/llm`):** Generate personalized email templates for campaigns using AI prompts.
*   **Follow-up Rules (`/followup-rules`):** CRUD operations for defining automated follow-up email rules.
*   **Tracking (`/track`):** Endpoint for tracking email opens via a pixel.

Refer to the API documentation (`/docs` or `/redoc` when the server is running) for detailed request/response schemas for each endpoint.
