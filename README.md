# LogPro API - v3.0
 
A Django REST API for viewing, filtering and exporting log file content.
Log data is stored in PostgreSQL for fast querying and filtering.
 
## Tech Stack
- Python
- Django & Django REST Framework
- PostgreSQL
- psycopg2-binary
- python-dotenv
- pytz
 
## Setup
 
1. Clone the repo
   git clone https://github.com/Arthur-IBS/IBS-project-back.git
   cd logpro
 
2. Create virtual environment
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
 
3. Install dependencies
   pip install -r requirements.txt
 
4. Create .env file
   Copy .env.example to .env and fill in your values
 
5. Create PostgreSQL database
   Open pgAdmin → create database named logpro_db
 
6. Run migrations
   python manage.py migrate
 
7. Start server
   python manage.py runserver
 
8. Configure log file location
   POST http://127.0.0.1:8000/api/config/
   Body: { "location": "path/to/your/logfile.log" }
 
9. Import log file into database (run once)
   python manage.py import_logs
 
## API Endpoints
 
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/logs/ | Fetch latest 1 hour of log content |
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
 
## Project Structure
 
logpro/
├── api/
│   ├── management/
│   │   └── commands/
│   │       └── import_logs.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── logpro/
│   ├── settings.py
│   └── urls.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── manage.py
 
## Log File Format
 
Expected log line format:
[DD.MM.YYYY HH:MM:SS], THREAD_ID, LEVEL , message
 
Example:
[13.05.2026 12:24:38], t9524, I  Server started
[13.05.2026 12:24:38], t9524, D  Loading configuration
[13.05.2026 12:24:38], t9524, W  High memory usage
[13.05.2026 12:24:38], t9524, E  Connection failed
 
## Notes
- Run import_logs once after setting up the log file location
- Sync runs automatically on every fetch request
- Time filters require date range to be set first
- Export requires date_from and date_to at minimum
GitHub - Arthur-IBS/IBS-project-back

 