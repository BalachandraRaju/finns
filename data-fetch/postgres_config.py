"""
PostgreSQL configuration for finns_auto database integration.
Handles database connection and migration from SQLite to PostgreSQL.
"""

import os
import sys
from typing import Optional
from logzero import logger

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class PostgreSQLConfig:
    """PostgreSQL configuration manager."""
    
    def __init__(self):
        self.postgres_url = self._get_postgres_url()
    
    def _get_postgres_url(self) -> Optional[str]:
        """Get PostgreSQL URL from environment or construct from components."""
        try:
            # Try direct DATABASE_URL first
            postgres_url = os.getenv("DATABASE_URL")
            
            if postgres_url and postgres_url.startswith("postgresql"):
                logger.info("✅ Found PostgreSQL URL in DATABASE_URL")
                return postgres_url
            
            # Try constructing from individual components
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5432")
            database = os.getenv("POSTGRES_DB", "finns_auto")
            username = os.getenv("POSTGRES_USER", "postgres")
            password = os.getenv("POSTGRES_PASSWORD", "")
            
            if password:
                constructed_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
                logger.info("✅ Constructed PostgreSQL URL from components")
                return constructed_url
            else:
                logger.warning("⚠️ No PostgreSQL password found in environment")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting PostgreSQL URL: {e}")
            return None
    
    def is_postgres_available(self) -> bool:
        """Check if PostgreSQL is available and accessible."""
        try:
            if not self.postgres_url:
                logger.warning("⚠️ No PostgreSQL URL configured")
                return False
            
            # Try to import required packages
            try:
                import psycopg2
            except ImportError:
                logger.error("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
                return False
            
            # Try to connect
            from sqlalchemy import create_engine
            
            engine = create_engine(self.postgres_url)
            
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                if result.fetchone():
                    logger.info("✅ PostgreSQL connection successful")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL (PostgreSQL if available, SQLite as fallback)."""
        if self.is_postgres_available():
            logger.info("🐘 Using PostgreSQL database")
            return self.postgres_url
        else:
            logger.info("📁 Falling back to SQLite database")
            return "sqlite:///./historical_data.db"
    
    def create_postgres_tables(self) -> bool:
        """Create tables in PostgreSQL database."""
        try:
            if not self.postgres_url:
                logger.error("❌ No PostgreSQL URL available")
                return False
            
            from sqlalchemy import create_engine
            from app.db import Base
            
            engine = create_engine(self.postgres_url)
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            
            logger.info("✅ PostgreSQL tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating PostgreSQL tables: {e}")
            return False
    
    def migrate_from_sqlite(self, sqlite_path: str = "./historical_data.db") -> bool:
        """Migrate data from SQLite to PostgreSQL (if needed)."""
        try:
            if not self.postgres_url:
                logger.error("❌ No PostgreSQL URL available for migration")
                return False
            
            if not os.path.exists(sqlite_path):
                logger.info("ℹ️ No SQLite database found, skipping migration")
                return True
            
            logger.info("🔄 Starting migration from SQLite to PostgreSQL...")
            
            from sqlalchemy import create_engine
            from app.models import Candle, LTPData, DataSyncStatus
            from app.db import SessionLocal
            
            # Create engines
            sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
            postgres_engine = create_engine(self.postgres_url)
            
            # Create sessions
            from sqlalchemy.orm import sessionmaker
            
            SQLiteSession = sessionmaker(bind=sqlite_engine)
            PostgresSession = sessionmaker(bind=postgres_engine)
            
            sqlite_session = SQLiteSession()
            postgres_session = PostgresSession()
            
            try:
                # Migrate Candles
                candles = sqlite_session.query(Candle).all()
                if candles:
                    logger.info(f"📊 Migrating {len(candles)} candle records...")
                    for candle in candles:
                        postgres_session.merge(candle)
                    postgres_session.commit()
                
                # Migrate LTP Data
                ltp_data = sqlite_session.query(LTPData).all()
                if ltp_data:
                    logger.info(f"💰 Migrating {len(ltp_data)} LTP records...")
                    for ltp in ltp_data:
                        postgres_session.merge(ltp)
                    postgres_session.commit()
                
                # Migrate Sync Status
                sync_data = sqlite_session.query(DataSyncStatus).all()
                if sync_data:
                    logger.info(f"🔄 Migrating {len(sync_data)} sync status records...")
                    for sync in sync_data:
                        postgres_session.merge(sync)
                    postgres_session.commit()
                
                logger.info("✅ Migration completed successfully")
                return True
                
            except Exception as e:
                postgres_session.rollback()
                logger.error(f"❌ Migration failed: {e}")
                return False
            finally:
                sqlite_session.close()
                postgres_session.close()
                
        except Exception as e:
            logger.error(f"❌ Error during migration: {e}")
            return False
    
    def setup_postgres_for_data_collection(self) -> bool:
        """Complete PostgreSQL setup for data collection."""
        try:
            logger.info("🔧 Setting up PostgreSQL for data collection...")
            
            # Check availability
            if not self.is_postgres_available():
                logger.error("❌ PostgreSQL not available")
                return False
            
            # Create tables
            if not self.create_postgres_tables():
                logger.error("❌ Failed to create PostgreSQL tables")
                return False
            
            # Migrate existing data if needed
            if not self.migrate_from_sqlite():
                logger.warning("⚠️ Migration from SQLite failed, but continuing...")
            
            logger.info("✅ PostgreSQL setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up PostgreSQL: {e}")
            return False

# Global instance
postgres_config = PostgreSQLConfig()
