"""
Django settings for server project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab

try:
    from config import *
except ImportError:
    print("未发现自定义配置，使用默认配置")
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-mlq6(#a^2vk!1=7=xhp#$i=o5d%namfs=+b26$m#sh_2rco7j^'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = locals().get("DEBUG", False)

# 如果前端是代理，则可以通过该配置，在系统构建url的时候，获取正确的 scheme
# 需要在 前端加入该配置  proxy_set_header X-Forwarded-Proto https;
# https://docs.djangoproject.com/zh-hans/4.2/ref/settings/#std-setting-SECURE_PROXY_SSL_HEADER
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ALLOWED_HOSTS = locals().get("ALLOWED_HOSTS", ["*"])

# Application definition

INSTALLED_APPS = [
    'daphne',  # 支持websocket
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'system.apps.SystemConfig',  # 系统管理
    'settings.apps.SettingsConfig',  # 设置相关
    'captcha.apps.CaptchaConfig',  # 图片验证码
    'message.apps.MessageConfig',  # websocket 消息
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'rest_framework',
    'django_filters',
    'django_celery_results',
    'django_celery_beat',
    'imagekit',
    'drf_yasg',
    *locals().get("XADMIN_APPS", []),
    'common.apps.CommonConfig',  # 这个放到最后, django ready
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'common.core.middleware.ApiLoggingMiddleware'
]

ROOT_URLCONF = 'server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

# WSGI_APPLICATION = 'server.wsgi.application'
ASGI_APPLICATION = "server.asgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Redis 配置
REDIS_HOST = locals().get("REDIS_HOST", "redis")
REDIS_PORT = locals().get("REDIS_PORT", 6379)
REDIS_PASSWORD = locals().get("REDIS_PASSWORD", "nineven")

DEFAULT_CACHE_ID = 1
CHANNEL_LAYERS_CACHE_ID = 2
CELERY_BROKER_CACHE_ID = 3
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{DEFAULT_CACHE_ID}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 8000},
            "PASSWORD": REDIS_PASSWORD,
            "DECODE_RESPONSES": True
        },
        "TIMEOUT": 60 * 15,
        "KEY_FUNCTION": "common.base.utils.redis_key_func",
        "REVERSE_KEY_FUNCTION": "common.base.utils.redis_reverse_key_func",
    },
}

# create database xadmin default character set utf8 COLLATE utf8_general_ci;
# grant all on xadmin.* to server@'127.0.0.1' identified by 'KGzKjZpWBp4R4RSa';
# python manage.py makemigrations
# python manage.py migrate
DATABASES = {
    'default': {
        'ENGINE': locals().get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': locals().get('DB_DATABASE', BASE_DIR / "db.sqlite3"),
        'HOST': locals().get('DB_HOST', 'mariadb'),
        'PORT': locals().get('DB_PORT', 3306),
        'USER': locals().get('DB_USER', 'server'),
        'PASSWORD': locals().get('DB_PASSWORD', 'KGzKjZpWBp4R4RSa'),
        'CONN_MAX_AGE': 600,
        # 设置MySQL的驱动
        # 'OPTIONS': {'init_command': 'SET storage_engine=INNODB'},
        # 'OPTIONS': {'init_command': 'SET sql_mode="STRICT_TRANS_TABLES"', 'charset': 'utf8mb4'},
        'OPTIONS': locals().get('OPTIONS', {}),
    }
}
# https://docs.djangoproject.com/zh-hans/5.0/topics/db/multi-db/#automatic-database-routing
# 读写分离 可能会出现 the current database router prevents this relation.
# 1.项目设置了router读写分离，且在ORM create()方法中，使用了前边filter()方法得到的数据，
# 2.由于django是惰性查询，前边的filter()并没有立即查询，而是在create()中引用了filter()的数据时，执行了filter()，
# 3.此时写操作的db指针指向write_db，filter()的db指针指向read_db，两者发生冲突，导致服务禁止了此次与mysql的交互
# 解决办法：
# 在前边filter()方法中，使用using()方法，使filter()方法立即与数据库交互，查出数据。
# Author.objects.using("default")
# >>> p = Person(name="Fred")
# >>> p.save(using="second")  # (statement 2)

DATABASE_ROUTERS = ['common.core.db.router.DBRouter']

# websocket 消息需要用到redis的消息发布订阅
CHANNEL_LAYERS = {
    "default": {
        # "BACKEND": "channels_redis.core.RedisChannelLayer",
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            "hosts": [f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{CHANNEL_LAYERS_CACHE_ID}"],
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True

AUTH_USER_MODEL = "system.UserInfo"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'api/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# STATICFILES_FINDERS = (
#     "django.contrib.staticfiles.finders.FileSystemFinder",
#     "django.contrib.staticfiles.finders.AppDirectoriesFinder"
# )
# 收集静态文件
# python manage.py collectstatic


# Media配置
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "upload")
FILE_UPLOAD_SIZE = 1024 * 1024 * 10
PICTURE_UPLOAD_SIZE = 1024 * 1024 * 0.5
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        # 'common.drf.renders.CSVFileRenderer', # 为什么注释：因为导入导出需要权限判断，在导入导出功能中再次自定义解析数据
        # 'common.drf.renders.ExcelFileRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'common.drf.parsers.AxiosMultiPartParser',
        'common.drf.parsers.CSVFileParser',
        'common.drf.parsers.ExcelFileParser',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'common.core.auth.CookieJWTAuthentication',
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",  # 允许basic授权，方便调试使用
    ],
    'EXCEPTION_HANDLER': 'common.core.exception.common_exception_handler',
    'DEFAULT_METADATA_CLASS': 'common.drf.metadata.SimpleMetadataWithFilters',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {  # {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        'anon': '60/m',
        'user': '600/m',
        'upload': '100/m',
        'download1': '10/m',
        'download2': '100/h',
        'register': '50/d',
        'reset_password': '50/d',
        'login': '50/h',
        **locals().get('DEFAULT_THROTTLE_RATES', {})
    },
    'DEFAULT_PAGINATION_CLASS': 'common.core.pagination.PageNumber',
    'DEFAULT_PERMISSION_CLASSES': [
        # 'rest_framework.permissions.IsAuthenticated',
        'common.core.permission.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'common.core.filter.BaseDataPermissionFilter',
    ),
}

# DRF扩展缓存时间
REST_FRAMEWORK_EXTENSIONS = {
    # 缓存时间
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 3600,
    # 缓存存储
    'DEFAULT_USE_CACHE': 'default',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=3600),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=15),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,  # 在登录的时候更新user表  last_login 字段

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': 'x',
    'ISSUER': 'server',
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('common.core.auth.ServerAccessToken',),
    # 'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'POST',
    'PUT',
)

CORS_ALLOW_HEADERS = (
    'XMLHttpRequest',
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-token"
)

# I18N translation
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# I18N 用于生成权限字段 label
PERMISSION_FIELD_LANGUAGE_CODE = 'zh'

BASE_LOG_DIR = os.path.join(BASE_DIR, "logs", "api")
TMP_LOG_DIR = os.path.join(BASE_DIR, "logs", "tmp")
CELERY_LOG_DIR = os.path.join(BASE_DIR, "logs", "task")
if not os.path.isdir(BASE_LOG_DIR):
    os.makedirs(BASE_LOG_DIR)
if not os.path.isdir(TMP_LOG_DIR):
    os.makedirs(TMP_LOG_DIR)
if not os.path.isdir(CELERY_LOG_DIR):
    os.makedirs(CELERY_LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(filename)s:%(funcName)s:%(lineno)d %(levelname)s] %(asctime)s %(process)d %(thread)d %(message)s'
        },
        'main': {
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'format': '%(asctime)s [%(filename)s:%(funcName)s:%(lineno)d %(levelname)s] %(message)s',
        },
        'exception': {
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'format': '\n%(asctime)s [%(levelname)s] %(message)s',
        },
        'simple': {
            'format': '[%(levelname)s][%(asctime)s][%(filename)s:%(funcName)s:%(lineno)d]%(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],  # 只有在Django debug为True时才在屏幕打印日志
            'class': 'logging.StreamHandler',
            'formatter': 'main'
        },
        'server': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，根据时间自动切
            'filename': os.path.join(BASE_LOG_DIR, "server.log"),  # 日志文件
            'maxBytes': 1024 * 1024 * 100,  # 日志大小 100M
            'backupCount': 10,  # 备份数为3
            # 'when': 'W6',  # 每天一切， 可选值有S/秒 M/分 H/小时 D/天 W0-W6/周(0=周一) midnight/如果没指定时间就默认在午夜
            'formatter': 'main',
            'encoding': 'utf-8',
        },
        'drf_exception': {
            'encoding': 'utf8',
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'exception',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 7,
            'filename': os.path.join(BASE_LOG_DIR, "drf_exception.log"),
        },
        'unexpected_exception': {
            'encoding': 'utf8',
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'exception',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 7,
            'filename': os.path.join(BASE_LOG_DIR, "unexpected_exception.log"),
        },
        'sql': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': os.path.join(BASE_LOG_DIR, "sql.log"),  # 日志文件
            'maxBytes': 1024 * 1024 * 50,  # 日志大小 50M
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        '': {  # 默认的logger应用如下配置
            'handlers': ['server', 'console', 'drf_exception', 'unexpected_exception'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['console', 'server'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console', 'server'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'sql'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'drf_exception': {
            'handlers': ['console', 'drf_exception'],
            'level': 'ERROR',
        },
        'unexpected_exception': {
            'handlers': ['console', 'unexpected_exception'],
            'level': 'ERROR',
        },
    },
}

CACHE_KEY_TEMPLATE = {
    'config_key': 'config',
    'make_token_key': 'make_token',
    'download_url_key': 'download_url',
    'pending_state_key': 'pending_state',
    'user_websocket_key': 'user_websocket',
    'upload_part_info_key': 'upload_part_info',
    'black_access_token_key': 'black_access_token',
    'common_resource_ids_key': 'common_resource_ids',
    **locals().get('CACHE_KEY_TEMPLATE', {})
}

# Celery Configuration Options
# https://docs.celeryq.dev/en/stable/userguide/configuration.html?
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# CELERY_RESULT_BACKEND = ''
# CELERY_CACHE_BACKEND = 'django-cache'

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'

# broker redis
DJANGO_DEFAULT_CACHES = CACHES['default']
CELERY_BROKER_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{CELERY_BROKER_CACHE_ID}'

# CELERY_WORKER_CONCURRENCY = 10  # worker并发数
CELERY_WORKER_AUTOSCALE = [10, 3]  # which needs two numbers: the maximum and minimum number of pool processes

CELERYD_FORCE_EXECV = True  # 非常重要,有些情况下可以防止死
CELERY_RESULT_EXPIRES = 3600 * 24 * 7  # 任务结果过期时间

CELERY_WORKER_DISABLE_RATE_LIMITS = True  # 任务发出后，经过一段时间还未收到acknowledge , 就将任务重新交给其他worker执行
CELERY_WORKER_PREFETCH_MULTIPLIER = 60  # celery worker 每次去redis取任务的数量

CELERY_WORKER_MAX_TASKS_PER_CHILD = 200  # 每个worker执行了多少任务就会死掉，我建议数量可以大一些，比如200

CELERY_ENABLE_UTC = False
DJANGO_CELERY_BEAT_TZ_AWARE = True

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# celery消息的序列化方式，由于要把对象当做参数所以使用pickle
# CELERY_RESULT_SERIALIZER = 'pickle'
# CELERY_ACCEPT_CONTENT = ['pickle']
# CELERY_TASK_SERIALIZER = 'pickle'

CELERY_BEAT_SCHEDULE = {
    'auto_clean_operation_job': {
        'task': 'system.tasks.auto_clean_operation_job',
        'schedule': crontab(hour='2', minute='2'),
        'args': ()
    },
    'auto_clean_expired_captcha_job': {
        'task': 'system.tasks.auto_clean_expired_captcha_job',
        'schedule': crontab(hour='2', minute='12'),
        'args': ()
    },
    'auto_clean_black_token_job': {
        'task': 'system.tasks.auto_clean_black_token_job',
        'schedule': crontab(hour='2', minute='22'),
        'args': ()
    },
    'auto_clean_tmp_file_job': {
        'task': 'system.tasks.auto_clean_tmp_file_job',
        'schedule': crontab(hour='2', minute='32'),
        'args': ()
    },
    **locals().get('CELERY_BEAT_SCHEDULE', {})
}

APPEND_SLASH = False

HTTP_BIND_HOST = '0.0.0.0'
HTTP_LISTEN_PORT = locals().get('HTTP_LISTEN_PORT', 8896)
# celery flower 任务监控配置
CELERY_FLOWER_PORT = 5566
CELERY_FLOWER_HOST = '127.0.0.1'
CELERY_FLOWER_AUTH = 'flower:flower123.'

CONFIG_IGNORE_APPS = ['daphne', 'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles', 'common',
                      'system', 'settings', 'message', 'rest_framework_simplejwt', 'token_blacklist', 'captcha',
                      'corsheaders', 'rest_framework', 'django_filters', 'django_celery_results', 'django_celery_beat',
                      'imagekit', 'drf_yasg']

# 访问白名单配置，无需权限配置
PERMISSION_WHITE_URL = [
    "^/api/system/login$",
    "^/api/system/logout$",
    "^/api/system/userinfo/self$",
    "^/api/system/user/notice/unread$",
    "^/api/system/routes$",
    "^/api/system/dashboard/",
    "^/api/system/.*choices$",
    "^/api/system/.*search-fields$",
]

# 前端权限路由 忽略配置
ROUTE_IGNORE_URL = [
    "^/api/system/.*choices$",  # 每个方法都有该路由，则忽略即可
    "^/api/system/.*search-fields$",  # 每个方法都有该路由，则忽略即可
    "^/api/system/.*search-columns$",  # 该路由使用list权限字段，无需重新配置
    "^/api/settings/.*search-columns$",  # 该路由使用list权限字段，无需重新配置
]

# 访问权限配置
PERMISSION_SHOW_PREFIX = [
    r'api/system',
    r'api/settings',
    r'api/flower',
    r'api-docs',
]
# 数据权限配置
PERMISSION_DATA_AUTH_APPS = [
    'system',
    'settings'
]

API_LOG_ENABLE = True
API_LOG_METHODS = ["POST", "DELETE", "PUT", "PATCH"]  # 'ALL'

# 忽略日志记录
API_LOG_IGNORE = {
    'system.OperationLog': ['GET']
}

# 在操作日志中详细记录的请求模块映射
API_MODEL_MAP = {
    "/api/system/refresh": "Token刷新",
    "/api/system/upload": "文件上传",
    "/api/system/login": "用户登录",
    "/api/system/logout": "用户登出",
    "/api/flower": "定时任务",
    "/api/system/password/send": "重置密码",
}

SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": True,
    "SECURITY_DEFINITIONS": {"Bearer": {"type": "apiKey", 'in': 'header', 'name': 'Authorization'}},
    'LOGIN_URL': '/api-docs/login/',
    'LOGOUT_URL': '/api-docs/logout/',
    # 'DOC_EXPANSION': None,
    # 'SHOW_REQUEST_HEADERS':True,
    # 'DOC_EXPANSION': 'list',
    # 接口文档中方法列表以首字母升序排列
    "APIS_SORTER": "alpha",
    # 如果支持json提交, 则接口文档中包含json输入框
    "JSON_EDITOR": True,
    # 方法列表字母排序
    "OPERATIONS_SORTER": "alpha",
    "VALIDATOR_URL": None,
    "AUTO_SCHEMA_TYPE": 2,  # 分组根据url层级分，0、1 或 2 层
    "DEFAULT_AUTO_SCHEMA_CLASS": "common.utils.swagger.CustomSwaggerAutoSchema",
}

# 密码安全配置
SECURITY_PASSWORD_MIN_LENGTH = 8
SECURITY_ADMIN_USER_PASSWORD_MIN_LENGTH = 8
SECURITY_PASSWORD_UPPER_CASE = True
SECURITY_PASSWORD_LOWER_CASE = True
SECURITY_PASSWORD_NUMBER = True
SECURITY_PASSWORD_SPECIAL_CHAR = False
SECURITY_PASSWORD_RULES = [
    'SECURITY_PASSWORD_MIN_LENGTH',
    'SECURITY_PASSWORD_UPPER_CASE',
    'SECURITY_PASSWORD_LOWER_CASE',
    'SECURITY_PASSWORD_NUMBER',
    'SECURITY_PASSWORD_SPECIAL_CHAR'
]

# 用户登录限制的规则
SECURITY_LOGIN_LIMIT_COUNT = 7
SECURITY_LOGIN_LIMIT_TIME = 30  # Unit: minute
# 登录IP限制的规则
SECURITY_LOGIN_IP_BLACK_LIST = []
SECURITY_LOGIN_IP_WHITE_LIST = []
SECURITY_LOGIN_IP_LIMIT_COUNT = 99999
SECURITY_LOGIN_IP_LIMIT_TIME = 30

# 登陆规则
SECURITY_LOGIN_ACCESS_ENABLED = True
SECURITY_LOGIN_CAPTCHA_ENABLED = True
SECURITY_LOGIN_ENCRYPTED_ENABLED = True
SECURITY_LOGIN_TEMP_TOKEN_ENABLED = True
SECURITY_LOGIN_BY_EMAIL_ENABLED = True
SECURITY_LOGIN_BY_SMS_ENABLED = False
SECURITY_LOGIN_BY_BASIC_ENABLED = True

# 注册规则
SECURITY_REGISTER_ACCESS_ENABLED = True
SECURITY_REGISTER_CAPTCHA_ENABLED = True
SECURITY_REGISTER_ENCRYPTED_ENABLED = True
SECURITY_REGISTER_TEMP_TOKEN_ENABLED = True
SECURITY_REGISTER_BY_EMAIL_ENABLED = True
SECURITY_REGISTER_BY_SMS_ENABLED = False
SECURITY_REGISTER_BY_BASIC_ENABLED = True
# 忘记密码规则
SECURITY_RESET_PASSWORD_ACCESS_ENABLED = True
SECURITY_RESET_PASSWORD_CAPTCHA_ENABLED = True
SECURITY_RESET_PASSWORD_TEMP_TOKEN_ENABLED = True
SECURITY_RESET_PASSWORD_ENCRYPTED_ENABLED = True
SECURITY_RESET_PASSWORD_BY_EMAIL_ENABLED = True
SECURITY_RESET_PASSWORD_BY_SMS_ENABLED = False

# 绑定邮箱
SECURITY_BIND_EMAIL_ACCESS_ENABLED = True
SECURITY_BIND_EMAIL_CAPTCHA_ENABLED = True
SECURITY_BIND_EMAIL_TEMP_TOKEN_ENABLED = True
SECURITY_BIND_EMAIL_ENCRYPTED_ENABLED = True

# 绑定手机
SECURITY_BIND_PHONE_ACCESS_ENABLED = True
SECURITY_BIND_PHONE_CAPTCHA_ENABLED = True
SECURITY_BIND_PHONE_TEMP_TOKEN_ENABLED = True
SECURITY_BIND_PHONE_ENCRYPTED_ENABLED = True

# 基本配置
SITE_URL = 'http://127.0.0.1:8000'

# 验证码配置
VERIFY_CODE_TTL = 5 * 60  # Unit: second
VERIFY_CODE_LIMIT = 60
VERIFY_CODE_LENGTH = 6
VERIFY_CODE_LOWER_CASE = False
VERIFY_CODE_UPPER_CASE = False
VERIFY_CODE_DIGIT_CASE = True

# 邮件配置
EMAIL_ENABLED = False
EMAIL_HOST = ""
EMAIL_PORT = 465
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_FROM = ""
EMAIL_RECIPIENT = ""
EMAIL_SUBJECT_PREFIX = "Xadmin-Server "
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False

# 短信配置
SMS_ENABLED = False
SMS_BACKEND = 'alibaba'
SMS_TEST_PHONE = ''

# 阿里云短信配置
ALIBABA_ACCESS_KEY_ID = ''
ALIBABA_ACCESS_KEY_SECRET = ''
ALIBABA_VERIFY_SIGN_NAME = ''
ALIBABA_VERIFY_TEMPLATE_CODE = ''

# 图片验证码
CAPTCHA_IMAGE_SIZE = (120, 40)  # 设置 captcha 图片大小
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'
CAPTCHA_LENGTH = 4  # 字符个数,仅针对随机字符串生效
CAPTCHA_TIMEOUT = 5  # 超时(minutes)
CAPTCHA_FONT_SIZE = 22
CAPTCHA_BACKGROUND_COLOR = "#ffffff"
CAPTCHA_FOREGROUND_COLOR = "#001100"
CAPTCHA_NOISE_FUNCTIONS = ("captcha.helpers.noise_arcs", "captcha.helpers.noise_dots")

# 下面图片验证码 默认配置
CAPTCHA_OUTPUT_FORMAT = '%(image)s %(text_field)s %(hidden_field)s '
# CAPTCHA_NOISE_FUNCTIONS = ("captcha.helpers.noise_arcs", "captcha.helpers.noise_dots")
# CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.random_char_challenge'
CAPTCHA_FONT_PATH = os.path.join(BASE_DIR, "captcha", "fonts", "Vera.ttf")
CAPTCHA_LETTER_ROTATION = (-35, 35)
CAPTCHA_FILTER_FUNCTIONS = ("captcha.helpers.post_smooth",)
CAPTCHA_PUNCTUATION = """_"',.;:-"""
CAPTCHA_FLITE_PATH = None
CAPTCHA_SOX_PATH = None
CAPTCHA_MATH_CHALLENGE_OPERATOR = "*"
CAPTCHA_GET_FROM_POOL = False
CAPTCHA_GET_FROM_POOL_TIMEOUT = 5
CAPTCHA_2X_IMAGE = True
