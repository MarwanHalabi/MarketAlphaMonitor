import schedule
import time
import logging
from etl import YahooETL
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_etl():
    """Run ETL process for all symbols"""
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_tracker")
        etl = YahooETL(database_url)
        results = etl.process_all_symbols()
        logger.info(f"ETL completed: {results}")
    except Exception as e:
        logger.error(f"ETL failed: {e}")

def cleanup_old_data():
    """Cleanup old data"""
    try:
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_tracker")
        etl = YahooETL(database_url)
        
        # Delete data older than 30 days
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        with etl.Session() as session:
            prices_deleted = session.execute(
                f"DELETE FROM prices WHERE ts < '{cutoff_date}'"
            ).rowcount
            
            indicators_deleted = session.execute(
                f"DELETE FROM indicators WHERE ts < '{cutoff_date}'"
            ).rowcount
            
            session.commit()
            logger.info(f"Cleanup completed: {prices_deleted} prices, {indicators_deleted} indicators deleted")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

def main():
    """Main scheduler function"""
    # Schedule ETL to run every 5 minutes
    schedule.every(5).minutes.do(run_etl)
    
    # Schedule cleanup to run daily at 2 AM.
    schedule.every().day.at("02:00").do(cleanup_old_data)
    
    # Run initial ETL
    run_etl()
    
    logger.info("Scheduler started. ETL will run every 5 minutes.")
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
