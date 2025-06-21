# AI-Powered Outreach Platform

## Overview

The AI-Powered Outreach Platform is a comprehensive solution designed to streamline and enhance email marketing campaigns. It empowers users to manage campaigns, import contacts via CSV, leverage AI to generate personalized email styles through an interactive chat interface, and automate email sending. The platform also includes features for follow-up sequences and basic email tracking.

This full-stack application combines a Python FastAPI backend with a Next.js (React) frontend, deployed on Render and Vercel respectively, offering a modern and scalable tool for intelligent email outreach.

## Core Features

- **User Authentication**: Secure signup and login functionality using JWT.
- **Campaign Management**: Create, list, and manage outreach campaigns.
- **Contact Import**: Easily import contacts into campaigns via CSV file upload.
- **AI-Powered Email Style Generation**: Interactive chat interface to collaboratively define email tone, style, and key messages with an AI assistant.
- **Personalized Email Template Creation**: Generate and store email templates (supporting `{{placeholder}}` variables) based on AI chat interactions or direct prompts.
- **Automated Email Sending**: Send personalized emails to campaign contacts using the defined templates.
- **Follow-Up Automation**: Define rules for automated follow-up emails based on conditions (e.g., not opened, not clicked). (Backend logic in place, frontend UI for management is a future enhancement).
- **Email Open Tracking**: Basic tracking of email open events using a pixel.
- **(Backend Ready, Frontend UI Future)**: Click tracking, detailed analytics, user profile management.

## Tech Stack

**Backend:**
- Python 3.9+
- FastAPI (for RESTful APIs)
- SQLAlchemy (ORM for database interaction)
- PostgreSQL (Relational Database)
- Alembic (Database migrations)
- Pydantic (Data validation and settings management)
- APScheduler (Background tasks, e.g., for follow-up processing)
- JWT (JSON Web Tokens for authentication)
- Integration with Large Language Models (LLMs) like OpenAI GPT (API key provided by user)
- `aiosmtplib` (for asynchronous email sending)

**Frontend:**
- Next.js (React Framework)
- TypeScript
- Axios (for API communication)
- Tailwind CSS (for styling - *assumption, please verify/update*)

**Deployment:**
- Backend: Render (or similar PaaS)
- Frontend: Vercel

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Node.js (v16.x or higher recommended) & npm or yarn
- PostgreSQL server (local or remote)
- Git

### Clone the Repository

```bash
git clone <your-repository-url>
cd <your-repository-directory>
```

## Backend Setup

1.  **Navigate to Backend Directory**:
    ```bash
    cd backend
    ```

2.  **Create and Activate Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables**:
    - Copy the example environment file (if one exists) or create a `.env` file in the `backend/` directory.
    - Populate it with the following required variables:
      ```env
      # backend/.env
      DATABASE_URL="postgresql+asyncpg://user:password@host:port/dbname" # Your PostgreSQL connection string
      JWT_SECRET="your_strong_random_jwt_secret"                       # Generate a strong secret key
      OPENAI_API_KEY="sk-your_openai_api_key"                          # Your OpenAI API key

      # SMTP Settings (e.g., for SendGrid, Mailgun, or Gmail for testing)
      SMTP_HOST="smtp.example.com"
      SMTP_PORT=587
      SMTP_USER="your_smtp_username"
      SMTP_PASSWORD="your_smtp_password"
      SMTP_SENDER_EMAIL="noreply@example.com" # Your default sender email
      SMTP_USE_TLS=True

      # Application Base URL (for links in emails, tracking pixels)
      APP_BASE_URL="http://localhost:8000" # For local development

      # Optional: Cloudflare R2 (if CSVs/file storage is moved to R2 later)
      # R2_BUCKET_NAME=""
      # R2_ACCOUNT_ID=""
      # R2_ACCESS_KEY_ID=""
      # R2_SECRET_ACCESS_KEY=""
      # R2_ENDPOINT_URL=""
      ```

5.  **Database Setup**:
    - Ensure your PostgreSQL server is running and accessible.
    - Create a new database for the application if you haven't already.
    - Update the `DATABASE_URL` in your `.env` file accordingly.
    - Run Alembic migrations to create/update the database schema:
      ```bash
      # Make sure you are in the backend/ directory with venv activated
      alembic upgrade head
      ```

6.  **Running the Backend Locally**:
    ```bash
    # From the backend/ directory
    uvicorn src.main:app --reload --port 8000
    ```
    The backend API should now be running at `http://localhost:8000`.

## Frontend Setup

1.  **Navigate to Frontend Directory**:
    ```bash
    cd frontend
    ```

2.  **Install Dependencies**:
    ```bash
    npm install
    # OR
    # yarn install
    ```

3.  **Environment Variables**:
    - Copy `frontend/.env.local.example` to `frontend/.env.local` (if the example file exists).
    - Create or update `frontend/.env.local` with the following:
      ```env
      # frontend/.env.local
      NEXT_PUBLIC_API_BASE_URL="http://localhost:8000" # Points to your local backend
      ```

4.  **Running the Frontend Locally**:
    ```bash
    npm run dev
    # OR
    # yarn dev
    ```
    The frontend application should now be running, typically at `http://localhost:3000`.

## Key API Endpoints

The backend exposes a RESTful API. Interactive API documentation (Swagger UI) is available at `/docs` and ReDoc at `/redoc` when the backend is running.

Key functional groups include:
- `/auth/` (signup, login)
- `/users/me/` (user profile)
- `/campaigns/` (CRUD for campaigns)
- `/campaigns/campaigns/upload` (CSV upload to create campaign & contacts - *path may need review for redundancy*)
- `/campaigns/{campaign_id}/send` (Initiate campaign sending)
- `/api/v1/ai-chat/conversation` (AI chat interaction)
- `/api/v1/ai-chat/finalize-style` (Finalize AI-generated style and create template)
- `/followup-rules/` (CRUD for follow-up rules)
- `/track/open/{tracking_id}.png` (Email open tracking pixel)
- `/llm/generate-campaign-template/` (Direct template generation via LLM)


## Deployment

**Backend (Render):**
- The backend is configured for deployment on Render using the `render.yaml` file.
- Connect your Git repository to a new "Web Service" on Render.
- Set the Build Command: `pip install --upgrade pip && pip install -r backend/requirements.txt && alembic -c backend/alembic.ini upgrade head` (or as defined in `render.yaml`).
- Set the Start Command: `uvicorn backend.src.main:app --host 0.0.0.0 --port $PORT` (or as defined in `render.yaml`).
- Configure all necessary environment variables (from the Backend Setup section) in the Render service dashboard.
- Render will also provision a PostgreSQL database if defined in `render.yaml`; its connection string will be injected as `DATABASE_URL`.

**Frontend (Vercel):**
- Connect your Git repository to a new Project on Vercel.
- Vercel should automatically detect it as a Next.js application.
- Set the Build Command (usually default): `next build` or `npm run build`.
- Output Directory (usually default): `.next`.
- Configure the `NEXT_PUBLIC_API_BASE_URL` environment variable in the Vercel project settings to point to your live Render backend URL.
