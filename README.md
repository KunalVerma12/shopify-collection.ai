# Shopify Collection AI

An AI-powered Shopify app for generating and managing collection descriptions using OpenAI.

The app retrieves Shopify collections, generates SEO-friendly descriptions with AI, allows users to review and edit the generated content, and provides an approval workflow before updating Shopify.

## ✨ Features

- 🛍️ Fetch Shopify collections through the Shopify Admin API
- 🤖 Generate collection descriptions using OpenAI
- ✏️ Review and edit AI-generated descriptions
- ✅ Approve descriptions before updating Shopify
- 🔐 Shopify embedded app authentication
- 🔑 Shopify App Bridge session-token authentication
- 🔄 Shopify OAuth token exchange for Admin API access
- ☁️ Vercel deployment support
- 🔒 Server-side handling of API credentials and secrets

## 🏗️ Architecture

```text
┌──────────────────────┐
│    Shopify Admin     │
│                      │
│    Embedded App      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    Shopify App       │
│      Bridge          │
│                      │
│    Session Token     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     Flask Backend    │
│                      │
│ Authentication       │
│ Collection API       │
│ AI Generation        │
│ Approval Workflow    │
└───────┬───────┬──────┘
        │       │
        ▼       ▼
┌───────────┐ ┌──────────────┐
│  OpenAI   │ │   Shopify    │
│    API    │ │  Admin API   │
└───────────┘ └──────────────┘
```

## 🔄 Workflow

```text
Shopify Collection
        │
        ▼
Retrieve Collection
        │
        ▼
Generate Description
        │
        ▼
AI Output
        │
        ▼
Review / Edit
        │
        ▼
Approve
        │
        ▼
Update Shopify
```

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend |
| Flask | REST API |
| Shopify Admin API | Shopify data and updates |
| Shopify App Bridge | Embedded app integration |
| OpenAI API | AI description generation |
| HTML / CSS / JavaScript | Frontend |
| Vercel | Production deployment |
| Git / GitHub | Version control |

## 📁 Project Structure

```text
shopify-collection-ai/
│
├── app/
│   ├── main.py
│   ├── shopify.py
│   ├── config.py
│   └── ...
│
├── public/
│   └── index.html
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 🔐 Environment Variables

Create a `.env` file in the project root.

```env
SHOPIFY_SHOP_URL=sarinskin.myshopify.com
SHOPIFY_CLIENT_ID=your_shopify_client_id
SHOPIFY_CLIENT_SECRET=your_shopify_client_secret
SHOPIFY_API_VERSION=2026-07

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
```

### Security

Never commit `.env` to GitHub.

The following credentials must remain private:

- Shopify Client Secret
- OpenAI API Key
- Shopify access tokens

Use `.env.example` as a template when configuring a new environment.

## 🚀 Local Development

Clone the repository:

```bash
git clone https://github.com/KunalVerma12/shopify-collection.ai.git
cd shopify-collection.ai
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

Add your Shopify and OpenAI credentials to `.env`.

Start the Flask application:

```bash
python -m app.main
```

The application will run locally on:

```text
http://localhost:5001
```

## 🌐 Production

The application is deployed using Vercel.

Production URL:

https://shopify-collection-ai.vercel.app

Production environment variables must be configured through the Vercel project settings.

## 🔑 Shopify Authentication

The application uses Shopify's embedded app authentication flow.

The frontend uses Shopify App Bridge to obtain a session token, which is sent to the Flask backend through the `Authorization` header.

The backend:

1. Receives the Shopify session token.
2. Validates the token.
3. Performs Shopify OAuth token exchange when required.
4. Obtains an offline Admin API access token.
5. Uses the access token for Shopify API requests.

Shopify credentials remain server-side and are never exposed to the frontend.

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config-check` | GET | Checks application configuration |
| `/api/collections` | GET | Retrieves Shopify collections |
| `/api/generate` | POST | Generates an AI collection description |
| `/api/approve` | POST | Approves and updates a collection |

Protected endpoints require a valid Shopify session token.

## 🤖 AI Generation

The application sends relevant collection information to OpenAI and generates a structured, customer-facing collection description.

Generated content can be reviewed and modified before being approved.

This keeps the workflow human-in-the-loop rather than automatically publishing AI-generated content without review.

## 🔒 Security

- Secrets are stored in environment variables.
- `.env` is excluded from version control.
- Shopify session tokens are validated server-side.
- Shopify Admin API access is performed by the backend.
- OpenAI API credentials are never exposed to the browser.
- Collection updates require explicit approval.

## 📌 Project Status

**Active Development**

The core application, Shopify integration, AI generation workflow, and production deployment are implemented. Authentication, UI, error handling, and production reliability are still being refined.

## 📄 License

This project is currently intended for private/internal use and is not licensed for redistribution.