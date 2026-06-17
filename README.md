# AI-Powered Outreach Platform

## Overview

The AI-Powered Outreach Platform is a comprehensive, full-stack solution designed to streamline and enhance email marketing campaigns. It empowers users to manage campaigns, import contacts via CSV, leverage AI to generate personalized email styles through an interactive chat interface, and automate email sending with intelligent follow-up sequences. The platform combines a Python FastAPI backend with a Next.js (React) frontend, offering a modern and scalable tool for intelligent email outreach.

## Core Features

- **User Authentication**: Secure signup and login functionality using JWT tokens for secure session management.

- **Campaign Management**: Create, organize, view, and manage outreach campaigns with full CRUD operations.

- **Contact Import**: Efficiently import contacts into campaigns via CSV file uploads for batch processing.

- **AI-Powered Email Style Generation**: Interactive chat interface that collaboratively works with an AI assistant to define email tone, style, and key messages. Users can engage in multi-turn conversations to refine their email approach.

- **Personalized Email Template Creation**: Automatically generate and store email templates based on AI chat interactions or direct LLM prompts, with support for dynamic personalization variables.

- **Automated Email Sending**: Send personalized emails at scale to campaign contacts using defined templates with variable substitution and async processing.

- **Intelligent Follow-Up Automation**: Define rules for automated follow-up emails based on conditions such as:
  - Email not opened
  - Email opened but not clicked
  - Custom time-based rules
  
  Backend logic fully implemented with APScheduler for background task processing.

- **Email Open Tracking**: Track email open events using tracking pixels embedded in email content, with automatic logging and analytics data collection.

- **Background Task Scheduling**: Automated processing of follow-up rules and scheduled tasks using APScheduler.

- **(Backend Ready, Frontend UI Future)**: Click tracking, detailed analytics dashboards, and user profile management.

## Tech Stack

**Backend:**
- Python 3.9+
- FastAPI - Modern, high-performance web framework for building REST APIs
- SQLAlchemy - Object-relational mapping for database interactions
- PostgreSQL - Production-grade relational database
- Alembic - Database schema versioning and migrations
- Pydantic - Data validation and settings management
- APScheduler - Advanced scheduling for background tasks and follow-ups
- JWT (JSON Web Tokens) - Secure authentication and authorization
- OpenAI GPT Integration - LLM API for email generation and AI chat
- aiosmtplib - Asynchronous SMTP client for efficient email delivery

**Frontend:**
- Next.js - React framework for server-side rendering and static generation
- TypeScript - Type-safe JavaScript for improved code quality
- Axios - HTTP client for API communication
- Tailwind CSS - Utility-first CSS framework for responsive design

## API Architecture

The backend exposes a comprehensive RESTful API organized by functional domains:

**Authentication & Users:**
- `/api/v1/auth/` - User signup, login, and token management
- `/api/v1/users/me/` - User profile retrieval and management

**Campaign Management:**
- `/api/v1/campaigns/` - CRUD operations for campaigns
- `/api/v1/campaigns/upload` - CSV file upload to bulk import contacts
- `/api/v1/campaigns/{campaign_id}/send` - Initiate campaign email sending

**AI Chat & Email Generation:**
- `/api/v1/ai-chat/conversation` - Multi-turn AI chat for email style definition
- `/api/v1/ai-chat/finalize-style` - Finalize AI-generated style and create email template
- `/api/v1/llm/generate-campaign-template/` - Direct template generation via LLM

**Follow-Up Automation:**
- `/api/v1/followups/rules/` - CRUD operations for follow-up automation rules

**Email Tracking:**
- `/api/v1/track/open/{tracking_id}.png` - Email open tracking pixel endpoint

Interactive API documentation (Swagger UI) is available at `/docs` and ReDoc documentation at `/redoc` when running the backend server.
