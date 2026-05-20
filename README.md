# LogPro API - v1.0
 
A Django REST API that serves log file content dynamically.
 
## Tech Stack
- Python
- Django
- Django REST Framework
- python-dotenv
 
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
 
5. Create log file
   mkdir logs
   echo "your log content" > logs/app.log
 
6. Run migrations
   python manage.py migrate
 
7. Start server
   python manage.py runserver
 
## API Endpoints
 
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/logs/ | Fetch log file content as JSON |
| GET | /api/logs/download/ | Download log file directly |
 
## Environment Variables
 
| Variable | Description |
|----------|-------------|
| LOG_FILE_PATH | Path to the log file e.g. logs/app.log |
 
## Project Structure
 
logpro/
├── api/
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── logpro/
│   ├── settings.py
│   └── urls.py
├── logs/
│   └── app.log
├── .env
├── .env.example
├── requirements.txt
└── manage.py
 