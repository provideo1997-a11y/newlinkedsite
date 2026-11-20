import os
from datetime import timedelta
class Config:
    SECRET_KEY=os.environ.get("SECRET_KEY","dev-only-change-me")
    DATABASE_URL=os.environ.get("DATABASE_URL","sqlite:///yakuza.db")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL=DATABASE_URL.replace("postgres://","postgresql+psycopg://",1)
    elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
        DATABASE_URL=DATABASE_URL.replace("postgresql://","postgresql+psycopg://",1)
    SQLALCHEMY_DATABASE_URI=DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME","admin")
    ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD","")
    COOKIE_SECURE=os.environ.get("COOKIE_SECURE","0").lower() in ("1","true","yes")
    SESSION_COOKIE_SECURE=COOKIE_SECURE
    SESSION_COOKIE_HTTPONLY=True
    SESSION_COOKIE_SAMESITE="Lax"
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES","30")))
    MAX_CONTENT_LENGTH=65536
    WTF_CSRF_TIME_LIMIT=3600
    PUBLIC_STATUS_LOOKUP=os.environ.get("PUBLIC_STATUS_LOOKUP","1")=="1"
