import uvicorn
import logging
from backend.app.core.database import engine, Base, ACTIVE_DB_TYPE
from backend.app.services.seed_data import seed_initial_data
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fashion_store")

def init_app():
    logger.info(f"Initializing VOGUE FIT Fashion E-Commerce...")
    logger.info(f"Active Database Engine: {ACTIVE_DB_TYPE}")
    
    # Create all schema tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")

    # Populate initial seed data
    with Session(engine) as db:
        seed_initial_data(db)

if __name__ == "__main__":
    init_app()
    print("=" * 60)
    print("🚀 VOGUE FIT - Fashion E-Commerce Server Starting...")
    print(f"🗄  Active Database: {ACTIVE_DB_TYPE}")
    print("🌐 Store URL: http://127.0.0.1:8080")
    print("📚 API Documentation: http://127.0.0.1:8080/docs")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8080, reload=True)
