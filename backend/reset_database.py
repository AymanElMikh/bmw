"""
Script to reset and reseed the database
Run with: python reset_database.py
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Delete and recreate the database"""
    from database import drop_db, init_db
    from database.seed import seed_database
    
    # Check if database exists
    db_file = "legal_billing.db"
    if os.path.exists(db_file):
        logger.info(f"Removing existing database: {db_file}")
        os.remove(db_file)
    
    # Recreate database
    logger.info("Creating new database...")
    init_db()
    
    # Seed data
    logger.info("Seeding database with initial data...")
    seed_database()
    
    logger.info("✅ Database reset complete!")

if __name__ == "__main__":
    try:
        reset_database()
    except Exception as e:
        logger.error(f"❌ Error resetting database: {e}")
        raise