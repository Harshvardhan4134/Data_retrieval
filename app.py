import os
import logging
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from pinecone import Pinecone
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

try:
    # Initialize Flask app and database
    db = SQLAlchemy(model_class=Base)
    app = Flask(__name__)

    # Check required environment variables
    required_vars = ["DATABASE_URL", "SESSION_SECRET", "OPENAI_API_KEY", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    app.config["UPLOAD_FOLDER"] = "uploads"

    # Initialize extensions
    logger.info("Initializing database...")
    db.init_app(app)

    logger.info("Setting up login manager...")
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Initialize OpenAI and Pinecone
    logger.info("Initializing AI services...")
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    pinecone_client = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    vector_db = pinecone_client.Index("document-embeddings")

    # Create upload directory if it doesn't exist
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Import routes after app initialization to avoid circular imports
    logger.info("Loading routes...")
    from routes import *

    # Initialize database and create tables
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()

except Exception as e:
    logger.error(f"Failed to initialize application: {str(e)}")
    raise