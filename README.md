# LeadForge — Lead Scoring & Triage API

LeadForge is a Python-based REST API that captures incoming leads, evaluates their purchase intent, detects potential spam, generates lead summaries and suggested replies, and stores lead information for retrieval.

 **Live API:** https://leadforge-api-ac06.onrender.com  
 **API Documentation:** https://leadforge-api-ac06.onrender.com/docs  
 **Health Check:** https://leadforge-api-ac06.onrender.com/health

## Features

- **Lead Management:** Create, retrieve, and list leads through REST API endpoints.
- **Lead Scoring:** Assign a score from 0 to 10 to help prioritize potential customers.
- **Spam Detection:** Flag potential spam leads.
- **Intent Classification:** Identify the lead's likely intent.
- **Automated Summaries:** Generate concise lead summaries and suggested replies.
- **Database Integration:** Store lead records using PostgreSQL in the deployed environment, with SQLite support for local development.
- **API Key Authentication:** Protect endpoints using the `X-API-Key` header.
- **Filtering and Pagination Controls:** Filter leads by minimum score and spam inclusion, and limit the number of results.
- **Optional Integrations:** Support for Anthropic-based scoring and HubSpot synchronization when configured.

## Tech Stack

- **Language:** Python
- **Backend:** FastAPI
- **Database:** PostgreSQL / SQLite
- **Data Validation:** Pydantic
- **API Documentation:** Swagger UI / OpenAPI
- **Deployment:** Render
- **Containerization:** Docker and Docker Compose
- **Testing:** pytest

## How It Works

```text
Website / Contact Form
         |
         v
   POST /leads
         |
         v
  Validate Lead Data
         |
         v
  Score & Classify Lead
   (Rules / Optional LLM)
         |
         v
  Store Lead in Database
         |
         v
  Return Lead Details
         |
         v
 Optional HubSpot Sync
```

## Live API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API health |
| POST | `/leads` | Create and score a lead |
| GET | `/leads` | Retrieve and filter leads |
| GET | `/leads/{lead_id}` | Retrieve a lead by ID |

All lead endpoints require the `X-API-Key` header.

### Example: Create a Lead

**Endpoint:** `POST /leads`

Request body:

```json
{
  "name": "Rahul Sharma",
  "email": "rahul.sharma@example.com",
  "phone": "9876543210",
  "message": "Interested in an enterprise subscription. Has a budget of 50000 and wants to start within 30 days.",
  "source": "Website"
}
```

Example response fields:

```json
{
  "id": 1,
  "name": "Rahul Sharma",
  "is_spam": false,
  "score": 6,
  "intent": "purchase enquiry",
  "summary": "Rahul Sharma wrote: Interested in an enterprise subscription",
  "scored_by": "rules",
  "crm_status": "skipped"
}
```

The example above illustrates the observed rules-based scoring response. Actual scores and integration statuses depend on the lead data and configuration.

### Example: Filter Leads

```http
GET /leads?min_score=5&include_spam=false&limit=10
```

Supported query parameters:

| Parameter | Description |
|---|---|
| `min_score` | Minimum score, from 0 to 10 |
| `include_spam` | Whether to include leads flagged as spam |
| `limit` | Maximum number of results, from 1 to 200 |

### Example: Retrieve a Lead

```http
GET /leads/1
```

Explore all endpoints and execute requests through the [Swagger UI](https://leadforge-api-ac06.onrender.com/docs).

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/shwetash77/Lead_Forge.git
cd Lead_Forge
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and configure the values needed for your environment.

```env
DATABASE_URL=sqlite:///./leadforge.db
LEADFORGE_API_KEY=replace_with_your_local_secret
ANTHROPIC_API_KEY=
HUBSPOT_TOKEN=
```

Use valid credentials and the database URL format supported by your application. Anthropic and HubSpot credentials are optional integrations. Never commit real secrets or API keys to GitHub.

### 5. Start the API

```bash
uvicorn app.main:app --reload
```

Open the local API documentation:

http://127.0.0.1:8000/docs

### Run with Docker

If Docker is installed and configured, you can also start the services using:

```bash
docker compose up --build
```

## Testing

Run the automated test suite with:

```bash
pytest
```

The repository includes tests for API behavior, authentication, scoring, and external integrations. External service tests are designed to use mocked HTTP responses.

## Configuration

| Environment variable | Purpose |
|---|---|
| `DATABASE_URL` | Database connection string |
| `LEADFORGE_API_KEY` | API authentication secret |
| `ANTHROPIC_API_KEY` | Optional LLM-based scoring |
| `LLM_MODEL` | Configured LLM model name |
| `HUBSPOT_TOKEN` | Optional HubSpot integration token |

Without an available LLM configuration, the application can use its rules-based scoring fallback. HubSpot synchronization requires valid configuration and successful integration execution.

## Future Improvements

- Build a dashboard for viewing and managing leads.
- Add notifications for high-priority leads.
- Improve CRM synchronization retries and monitoring.
- Add database migrations for production deployments.
- Integrate a website contact form or WordPress plugin.

## Author

**Sweta Sharma**

GitHub: https://github.com/shwetash77

---

*This project demonstrates REST API development, authentication, database integration, automated testing, lead prioritization, and cloud deployment.*
