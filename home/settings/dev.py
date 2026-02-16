'''Use this for development'''

from .base import *

ALLOWED_HOSTS += ['127.0.0.1']
DEBUG = True

WSGI_APPLICATION = 'home.wsgi.dev.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

CORS_ORIGIN_WHITELIST = (
    'http://localhost:3000',
    'http://localhost:3001',
)

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISH_KEY = os.getenv("STRIPE_PUBLISH_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")