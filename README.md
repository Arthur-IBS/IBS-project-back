# LogPro API - v4.0

A Django REST API for viewing, filtering and exporting log file content.
Log data is ingested via a Python agent into Logstash and stored in Elasticsearch for fast querying and filtering.

## Tech Stack
- Python
- Django & Django REST Framework
- PostgreSQL (LogConfig only)
- Elasticsearch 9.4.2
- Logstash 9.4.2
- elasticsearch-py
- psycopg2-binary
- python-dotenv
- pytz

## Architecture

```
Log File
  → agent.py (reads every 60s)
  → Logstash (TCP port 5000, parses & transforms)
  → Elasticsearch (stores & indexes)
  → Django REST API (queries ES)
  → React Frontend (displays)
```

## Setup

1. Clone the repo
   ```
   git clone https://github.com/Arthur-IBS/IBS-project-back.git
   cd logpro
   ```

2. Create virtual environment
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Create .env file
   Copy .env.example to .env and fill in your values

5. Create PostgreSQL database
   Open pgAdmin → create database named `logpro`

6. Run migrations
   ```
   python manage.py migrate
   ```

7. Start Elasticsearch
   ```
   cd path/to/elasticsearch/bin
   elasticsearch.bat             # Windows
   ./elasticsearch               # Mac/Linux
   ```

8. Start Logstash
   ```
   cd path/to/logstash/bin
   logstash.bat -f path/to/logpro/logstash.conf    # Windows
   ./logstash -f path/to/logpro/logstash.conf      # Mac/Linux
   ```

9. Start Django server
   ```
   python manage.py runserver
   ```

10. Configure log file location
    ```
    POST http://127.0.0.1:8000/api/config/
    Body: { "location": "path/to/your/logfile.log" }
    ```

11. Start agent (reads log file and sends to Logstash)
    ```
    python agent.py
    ```

## Running Order

| Order | Service | Command |
|-------|---------|---------|
| 1 | Elasticsearch | elasticsearch.bat |
| 2 | Logstash | logstash.bat -f logstash.conf |
| 3 | Django | python manage.py runserver |
| 4 | Agent | python agent.py |
| 5 | React | npm start |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/logs/ | Fetch log content from Elasticsearch |
| GET | /api/logs/export/ | Export filtered logs as CSV |
| POST | /api/config/ | Set log file location |
| PUT | /api/config/ | Update log file location |

## Query Parameters for GET /api/logs/

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| page | integer | Page number for pagination | ?page=2 |
| levels | string | Filter by log level (comma separated) | ?levels=W,E |
| date_from | string | Filter from date (YYYY-MM-DD) | ?date_from=2026-05-13 |
| date_to | string | Filter to date (YYYY-MM-DD) | ?date_to=2026-05-13 |
| time_from | string | Filter from time (HH:MM) requires date | ?time_from=10:00 |
| time_to | string | Filter to time (HH:MM) requires date | ?time_to=12:00 |

## Query Parameters for GET /api/logs/export/

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| date_from | string | Start date (YYYY-MM-DD) | Yes |
| date_to | string | End date (YYYY-MM-DD) | Yes |
| time_from | string | Start time (HH:MM) | No |
| time_to | string | End time (HH:MM) | No |
| levels | string | Log levels (comma separated) | No |

## Log Levels

| Level | Description |
|-------|-------------|
| I | Info |
| D | Debug |
| W | Warning |
| E | Error |

## Environment Variables

| Variable | Description |
|----------|-------------|
| DB_NAME | PostgreSQL database name |
| DB_USER | PostgreSQL username |
| DB_PASSWORD | PostgreSQL password |
| DB_HOST | Database host (localhost) |
| DB_PORT | Database port (5432) |
| SECRET_KEY | Django secret key |
| DEBUG | Debug mode (True/False) |

## Elasticsearch Details

| Setting | Value |
|---------|-------|
| Host | http://localhost:9200 |
| Index | logpro-logs |
| Auth | None (security disabled) |

## Project Structure

```
logpro/
├── api/
│   ├── models.py          # LogConfig only (LogEntry removed)
│   ├── serializers.py     # LogConfigSerializer only
│   ├── views.py           # Queries Elasticsearch
│   └── urls.py
├── logpro/
│   ├── settings.py
│   └── urls.py
├── agent.py               # Reads log file → sends to Logstash every 60s
├── logstash.conf          # Logstash pipeline config
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── manage.py
```

## Log File Format

Expected log line format:
```
[DD.MM.YYYY HH:MM:SS], THREAD_ID, LEVEL MESSAGE
```

Example:
```
[13.05.2026 12:24:38], t9524, I Server started
[13.05.2026 12:24:38], t9524, D Loading configuration
[13.05.2026 12:24:38], t9524, W High memory usage
[13.05.2026 12:24:38], t9524, E Connection failed
```

## Notes
- `agent.py` runs every 60 seconds and only reads new lines since last run
- Position is tracked in `agent_position.txt` (excluded from git)
- Time filters require date range to be set first
- Export requires `date_from` and `date_to` at minimum
- To reset and re-index all logs: delete ES index, delete `agent_position.txt`, restart agent
