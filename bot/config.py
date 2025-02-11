import logging
from urllib.parse import quote

BOT_TOKEN = "7980873571:AAGTmAGCcT0nDDjYYPmsvw8j1vu4sY0ZUlc"
ADMIN_ID = "322690337"

LOG_LEVEL = "INFO"
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logging.info("Логирование настроено")

DB_CONFIG = {
    "dbname": "mydatabase",
    "user": "myuser",
    "password": "mypassword",
    "host": "db",
    "port": "5432"
}

REPORT_FOLDER = "reports/"
