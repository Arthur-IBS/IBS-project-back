# LogPro API - v1.0

A Django REST API for viewing, filtering and exporting application log content.
Log data is ingested via a Python agent into Logstash and stored in Elasticsearch for fast querying and filtering.

## Tech Stack

- Python
- Django & Django REST Framework
- PostgreSQL (LogConfig only — stores app configurations)
- Elasticsearch 9.4.2
- Logstash 9.4.2
- elasticsearch-py
- psycopg2-binary
- python-dotenv
- pytz
- djangorestframework-simplejwt (JWT authentication)
- drf-spectacular (Swagger docs)

## Architecture

```
Log File
  → agent.py (reads new lines every 60s)
  → Logstash (HTTP port 5000, parses & transforms)
  → Elasticsearch (stores & indexes per app)
  → Django REST API (queries ES, JWT protected)
  → React Frontend (displays with filters)
```

## Setup

### 1. Clone the repo
```
git clone https://github.com/Arthur-IBS/IBS-project-back.git
cd logpro
```

### 2. Create virtual environment
```
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Create `.env` file
Copy `.env.example` to `.env` and fill in your values.

### 5. Create PostgreSQL database
Open pgAdmin → create database named `logpro_db`

### 6. Run migrations
```
python manage.py migrate
```

### 7. Create superuser (for JWT login)
```
python manage.py createsuperuser
```

### 8. Start Elasticsearch
```
cd path/to/elasticsearch/bin
.\elasticsearch.bat          # Windows
./elasticsearch              # Mac/Linux
```
Wait until cluster health turns GREEN.

### 9. Start Logstash
```
cd path/to/logstash/bin
.\logstash.bat -f path/to/logpro/logstash.conf    # Windows
./logstash -f path/to/logpro/logstash.conf         # Mac/Linux
```
Wait until you see `Pipelines running`.

### 10. Start Django server
```
python manage.py runserver
```

### 11. Configure app location
```
POST http://127.0.0.1:8000/api/config/
Headers: Authorization: Bearer <token>
Body:
{
  "app_name": "opsman",
  "location": "C:/path/to/your/logfile.log",
  "log_format": "opsman",
  "es_index": "logpro-opsman"
}
```

### 12. Start agent
```
python agent.py
```

---

## Running Order

| Order | Service | Command |
|-------|---------|---------|
| 1 | Elasticsearch | `elasticsearch.bat` |
| 2 | Logstash | `logstash.bat -f logstash.conf` |
| 3 | Django | `python manage.py runserver` |
| 4 | Agent | `python agent.py` |
| 5 | React | `npm start` |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/token/ | No | Get JWT access + refresh tokens |
| POST | /api/token/refresh/ | No | Refresh access token |
| GET | /api/logs/ | Yes | Fetch log content from Elasticsearch |
| GET | /api/logs/export/ | Yes | Export filtered logs as CSV |
| GET | /api/apps/ | Yes | List all configured applications |
| GET | /api/config/ | Yes | List all app configs |
| POST | /api/config/ | Yes | Add new app config |
| PUT | /api/config/ | Yes | Update existing app config |
| GET | /api/docs/ | No | Swagger UI documentation |
| GET | /api/schema/ | No | OpenAPI schema |

---

## Authentication

All endpoints except `/api/token/` and `/api/docs/` require JWT authentication.

**Get token:**
```
POST /api/token/
Body: { "username": "your_username", "password": "your_password" }
```

**Use token:**
```
Headers: Authorization: Bearer <access_token>
```

---

## Query Parameters for GET /api/logs/

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| app | string | Application name | ?app=opsman |
| page | integer | Page number | ?page=2 |
| levels | string | Filter by level (comma separated) | ?levels=W,E |
| date_from | string | Start date (YYYY-MM-DD) | ?date_from=2026-05-13 |
| date_to | string | End date (YYYY-MM-DD) | ?date_to=2026-05-13 |
| time_from | string | Start time HH:MM (requires date) | ?time_from=10:00 |
| time_to | string | End time HH:MM (requires date) | ?time_to=12:00 |

---

## Query Parameters for GET /api/logs/export/

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| app | string | No | Application name |
| date_from | string | Yes | Start date (YYYY-MM-DD) |
| date_to | string | Yes | End date (YYYY-MM-DD) |
| time_from | string | No | Start time (HH:MM) |
| time_to | string | No | End time (HH:MM) |
| levels | string | No | Log levels (comma separated) |

---

## Log Levels

| Level | Description |
|-------|-------------|
| I | Info |
| D | Debug |
| W | Warning |
| E | Error |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| SECRET_KEY | Django secret key |
| DEBUG | Debug mode (True/False) |
| DB_NAME | PostgreSQL database name |
| DB_USER | PostgreSQL username |
| DB_PASSWORD | PostgreSQL password |
| DB_HOST | Database host |
| DB_PORT | Database port |
| ES_HOST | Elasticsearch host URL |
| ES_INDEX_PREFIX | ES index prefix (default: logpro) |
| LOGSTASH_HOST | Logstash host |
| LOGSTASH_PORT | Logstash HTTP input port |
| AGENT_LOG_FILE | Full path to log file |
| AGENT_POSITION_FILE | Position tracker file name |
| AGENT_INTERVAL_SECONDS | How often agent runs (seconds) |
| AGENT_MAX_RETRIES | Max retry attempts on failure |
| AGENT_RETRY_DELAY | Seconds between retries |
| APP_NAME | Application name (used as ES index suffix) |

---

## Adding a New Application

### 1. Create `.env.appname` in logpro folder:
```
APP_NAME=appname
AGENT_LOG_FILE=C:/path/to/appname.log
AGENT_POSITION_FILE=agent_position_appname.txt
LOGSTASH_HOST=localhost
LOGSTASH_PORT=5000
AGENT_INTERVAL_SECONDS=60
AGENT_MAX_RETRIES=3
AGENT_RETRY_DELAY=5
```

### 2. Add app config via API:
```
POST /api/config/
Body:
{
  "app_name": "appname",
  "location": "C:/path/to/appname.log",
  "log_format": "appname",
  "es_index": "logpro-appname"
}
```

### 3. Add date format to `logstash.conf`:
```
} else if [application] == "appname" {
  date {
    match => ["log_timestamp", "yyyy-MM-dd HH:mm:ss"]
    target => "@timestamp"
    timezone => "Asia/Kolkata"
  }
}
```

### 4. Run agent for new app:
```
python agent.py --env .env.appname
```

### 5. Restart Logstash to pick up new config.

---

## Elasticsearch Details

| Setting | Value |
|---------|-------|
| Host | http://localhost:9200 |
| Index pattern | logpro-{app_name} |
| Auth | None (security disabled for local dev) |
| Version | 9.4.2 |

---

## Project Structure

```
logpro/
├── api/
│   ├── management/
│   │   └── commands/
│   │       └── import_logs.py    # legacy one-time import (reference only)
│   ├── migrations/
│   ├── models.py                 # LogConfig model
│   ├── serializers.py
│   ├── views.py                  # queries Elasticsearch
│   └── urls.py
├── logpro/
│   ├── settings.py
│   └── urls.py
├── agent.py                      # reads log file → sends to Logstash every 60s
├── logstash.conf                 # Logstash pipeline config
├── log_generator.py              # fake log generator for testing
├── .env.example
├── .gitignore
├── requirements.txt
└── manage.py
```

---

## Log File Format

Expected log line format:
```
 [DD.MM.YYYY HH:MM:SS], tTHREAD_ID, LEVEL  message
```

Example:
```
 [13.05.2026 12:24:38], t9524, I  Server started
 [13.05.2026 12:24:38], t9524, D  Loading configuration
 [13.05.2026 12:24:38], t9524, W  High memory usage
 [13.05.2026 12:24:38], t9524, E  Connection failed
```

---

## Notes

- `agent.py` reads only new lines since last run (tracked via `agent_position.txt`)
- `agent_position.txt` is excluded from git
- Time filters require date range to be set first
- Export requires `date_from` and `date_to` at minimum
- Each app gets its own Elasticsearch index (`logpro-{app_name}`)
- To reset and re-index all logs: delete ES index, delete `agent_position.txt`, restart agent
- Swagger UI available at `/api/docs/`
