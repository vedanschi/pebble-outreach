# AI-Powered Outreach Application Frontend

## Overview

This project is the frontend for an AI-powered email outreach application, designed to work seamlessly with the backend API. It provides a user-friendly interface for managing campaigns, authenticating users, uploading contacts via CSV, generating personalized email templates, and managing follow-up rules. The goal is to create an intuitive experience that leverages AI to enhance outreach efforts.

## Tech Stack

- **Framework:** Next.js (React)
- **Language:** TypeScript
- **Styling:** CSS Modules / Global CSS
- **State Management:** React Context API (or any preferred state management library)
- **API Integration:** Axios or Fetch API for making requests to the backend

## Getting Started

These instructions will guide you through setting up and running the frontend application locally.

### Prerequisites

- Node.js (version 14 or higher)
- npm or yarn
- Access to the backend API

### 1. Clone the Repository

```bash
# git clone <repository_url> # Replace with your repo URL
# cd ai-outreach-frontend
```

### 2. Install Dependencies

Install all required packages:

```bash
npm install
# or
yarn install
```

### 3. Set Up Environment Variables

Create a `.env.local` file in the root of the project to store your environment variables. You can use the `.env.local.example` file as a reference.

### 4. Running the Application

You can run the Next.js application in development mode using:

```bash
npm run dev
# or
yarn dev
```

The application should now be accessible at `http://localhost:3000`.

### 5. Building for Production

To build the application for production, run:

```bash
npm run build
# or
yarn build
```

Then, you can start the production server with:

```bash
npm start
# or
yarn start
```

## Folder Structure

- **public/**: Contains static assets like images and the favicon.
- **src/**: Main source directory for the application.
  - **components/**: Contains reusable components for authentication, campaigns, CSV upload, email generation, and follow-ups.
  - **pages/**: Contains the application routes and pages.
  - **styles/**: Contains global styles for the application.
  - **utils/**: Contains utility functions for API calls.
  - **types/**: Contains TypeScript types and interfaces.

## Features

- **User Authentication**: Login and signup forms for user management.
- **Campaign Management**: Create, view, and manage campaigns.
- **CSV Upload**: Upload CSV files for importing contacts.
- **Email Generation**: Generate personalized email templates using AI.
- **Follow-Up Management**: Create and manage follow-up rules for campaigns.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.