"""
Django settings for agro_market project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
import dj_database_url

# Load environment variables
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
# Security
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,.onrender.com,aiagrosystem.onrender.com').split(',')



# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# MPESA Configuration
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE')
MPESA_SHORTCODE_TYPE = os.environ.get('MPESA_SHORTCODE_TYPE')
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL')
MPESA_ENVIRONMENT = os.environ.get('MPESA_ENVIRONMENT')
MPESA_INITIATOR_NAME = os.environ.get('MPESA_INITIATOR_NAME')
MPESA_INITIATOR_PASSWORD = os.environ.get('MPESA_INITIATOR_PASSWORD')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'cloudinary_storage',
    'cloudinary',
    'whitenoise.runserver_nostatic',
    'crispy_forms',
    'crispy_bootstrap5',
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'accounts',
    'marketplace',
    'ai_predictions',
    'transactions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'accounts.middleware.DuplicateUsernameMiddleware',
]

ROOT_URLCONF = 'agro_market.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'agro_market.wsgi.application'
ASGI_APPLICATION = 'agro_market.asgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files - Cloudinary
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)

MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Allauth
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_MIN_LENGTH = 3

# Custom allauth forms
ACCOUNT_FORMS = {
    'signup': 'accounts.forms.CustomSignupForm',
}

SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_UNIQUE_EMAIL = True

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}


# Add to agro_market/settings.py (at the bottom)

# Groq API Configuration (Free alternative to OpenAI)
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
