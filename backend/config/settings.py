"""
Django settings for Satori Accounting System.
Multi-tenant configuration for Colombian accounting requirements.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url
import django.utils.encoding

# Patch force_text for django-fernet-fields compatibility with Django 4.0+
django.utils.encoding.force_text = django.utils.encoding.force_str

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SATORI SECURITY CONFIGURATION
# Key for sensitive data encryption (Certificates passwords, etc)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

if ENCRYPTION_KEY:
    FERNET_KEYS = [ENCRYPTION_KEY]
else:
    # Durante el build (collectstatic), generar una clave temporal
    # En runtime, si no existe la variable, el sistema fallará apropiadamente
    import sys
    is_collectstatic = 'collectstatic' in sys.argv
    if is_collectstatic:
        # Clave temporal solo para el build - no se usa en producción
        from cryptography.fernet import Fernet
        FERNET_KEYS = [Fernet.generate_key().decode()]
    else:
        print("⚠️ ADVERTENCIA: No se encontró ENCRYPTION_KEY. Los campos encriptados fallarán.")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-development-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:3000').split(',')
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    # 'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    
    # Project apps
    'apps.common',
    'apps.core',
    'apps.treasury',
    'apps.accounting',
    'apps.invoicing',
    'apps.support_docs',
    'apps.taxes',
    'apps.dian',
    'apps.reports',
    'apps.payroll',
    'apps.sync',
    'apps.tenants',  # Enabled for Client model
    'apps.electronic_events', # RADIAN
    'apps.health_checks',

    # Auth & SSO
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
]

SITE_ID = 1

# Auth Config
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Social Account Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_SECRET'),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'microsoft': {
        'TENANT': 'common',
    }
}

ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = 'apps.core.adapters.MySocialAccountAdapter'

# Evitar que solucite Username
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True

LOGIN_REDIRECT_URL = '/api/auth/social/callback/'  # Internal redirect to View for token exchange
LOGOUT_REDIRECT_URL = '/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',

    # --- HOTFIX: AISLAMIENTO MULTI-TENANT ---
    # Se inserta después de la autenticación pero ANTES de las vistas.
    'apps.tenants.middleware.TenantMiddleware',
    # ----------------------------------------
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'satori_db'),
        'USER': os.getenv('DB_USER', 'satori_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'satori_pass'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Fallback to SQLite if configured (Optional - for local dev without Postgres)
if os.getenv('USE_SQLITE', 'False') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# DATABASE_ROUTERS = [
#     'django_tenants.routers.TenantSyncRouter',
# ]

# Multi-tenant Configuration (commented out for now)
# TENANT_MODEL = "tenants.Client"
# TENANT_DOMAIN_MODEL = "tenants.Domain"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    # 'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:8080'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:3000'
).split(',')

# Celery Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# DIAN Configuration (Colombian Electronic Invoicing)
DIAN_CONFIG = {
    'TEST_MODE': os.getenv('DIAN_TEST_MODE', 'True') == 'True',
    'SOFTWARE_ID': os.getenv('DIAN_SOFTWARE_ID', ''),
    'SOFTWARE_PIN': os.getenv('DIAN_SOFTWARE_PIN', ''),
    'CERTIFICATE_PATH': os.getenv('DIAN_CERTIFICATE_PATH', ''),
    'CERTIFICATE_PASSWORD': os.getenv('DIAN_CERTIFICATE_PASSWORD', ''),
    'NIT': os.getenv('DIAN_NIT', ''),
    'WEBSERVICE_URL': os.getenv(
        'DIAN_WEBSERVICE_URL',
        'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc'
    ),
    # Test environment endpoints
    'TEST_WEBSERVICE_URL': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc',
    # Production environment endpoints
    'PROD_WEBSERVICE_URL': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc',
}

# Cali Municipality Configuration
CALI_CONFIG = {
    'MUNICIPALITY_CODE': '76001',
    'MUNICIPALITY_NAME': 'Santiago de Cali',
    'DEPARTMENT_CODE': '76',
    'DEPARTMENT_NAME': 'Valle del Cauca',
    'ICA_TAX_RATE': float(os.getenv('CALI_ICA_TAX_RATE', '0.00966')),  # 9.66 por mil
}

# Colombian Tax Configuration
TAX_CONFIG = {
    'IVA_GENERAL': 0.19,  # 19%
    'IVA_REDUCED_5': 0.05,  # 5%
    'IVA_EXCLUDED': 0.0,  # 0%
    'RETEFUENTE_SERVICES': 0.04,  # 4%
    'RETEIVA': 0.15,  # 15% del IVA
    'RETEICA_CALI': 0.00966,  # 9.66 por mil
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Satori Accounting System API',
    'DESCRIPTION': 'Sistema Contable Multi-tenant con Facturación Electrónica DIAN',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'satori.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# Supress Cross-Origin-Opener-Policy warning in HTTP
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

