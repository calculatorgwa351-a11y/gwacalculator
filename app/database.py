from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import ssl
import certifi

# Database Configuration
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Database configuration
    PGUSER = os.getenv('PGUSER')
    PGPASSWORD = os.getenv('PGPASSWORD')
    PGHOST = os.getenv('PGHOST')
    PGPORT = os.getenv('PGPORT', '5432')
    PGDATABASE = os.getenv('PGDATABASE')
    SUPABASE_SSL_NO_VERIFY = os.getenv('SUPABASE_SSL_NO_VERIFY', '0').lower() in ("1", "true", "yes")
    
    @property
    def database_url(self):
        if self.PGUSER and self.PGPASSWORD and self.PGHOST and self.PGPORT and self.PGDATABASE:
            # Use PostgreSQL (Supabase)
            if self.SUPABASE_SSL_NO_VERIFY:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            else:
                ctx = ssl.create_default_context(cafile=certifi.where())
            
            return f"postgresql+pg8000://{self.PGUSER}:{self.PGPASSWORD}@{self.PGHOST}:{self.PGPORT}/{self.PGDATABASE}?ssl_context={ctx}"
        else:
            # Use SQLite for local development
            return "sqlite:///gwa_calculator.db"

config = Config()

# Database setup
engine = create_engine(config.database_url, pool_pre_ping=True, pool_recycle=300, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
