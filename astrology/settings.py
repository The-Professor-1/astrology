import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-ko!nbxq^_s2&)o^4w!ya+t_)9u_25zcmdh)u3@hq26knoz$p*d')
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,sinekewakibt-git-main-the-professor-1s-projects.vercel.app,sinekewakibt-ozj7o11tf-the-professor-1s-projects.vercel.app,sinekewakibt.vercel.app').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'calculator',
    'widget_tweaks',
    'contactus',
    'blog',
    'home',
    'aboutus',
]

MIDDLEWARE = [
     "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'astrology.urls'
CSRF_TRUSTED_ORIGINS = ['https://sinekewakibt.vercel.app',]
CSRF_COOKIE_DOMAIN = '.sinekewakibt.vercel.app'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'astrology.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'neondb'),
        'USER': os.getenv('DB_USER', 'neondb_owner'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'npg_npXoUD4arN8I'),
        'HOST': os.getenv('DB_HOST', 'ep-flat-frog-a5axh07n-pooler.us-east-2.aws.neon.tech'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {'sslmode': 'require'}
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

MEDIA_ROOT = '/tmp/'  # Where uploaded files are saved
MEDIA_URL = '/media/'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# For local development
SESSION_COOKIE_DOMAIN = os.getenv('SESSION_DOMAIN', None) # Ensure the leading dot for subdomains
SESSION_COOKIE_PATH = '/'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Ensure you're using the DB backend

LOGIN_URL = '/home/login/'  # Or wherever your login view is located
LOGIN_REDIRECT_URL = '/home/'  # Redirect after login
LOGOUT_REDIRECT_URL = '/home/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'