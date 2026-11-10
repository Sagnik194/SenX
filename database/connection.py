
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import DATABASE_URL, DB_SSL_CA


connect_args = {}

# Enable certificate-verified SSL when configured.
if DB_SSL_CA:
    connect_args["ssl"] = {
        "ca": DB_SSL_CA
    }


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    connect_args=connect_args,
    echo=False
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT VERSION()")
            )

            version = result.scalar()

            return {
                "success": True,
                "message": "MySQL connection successful.",
                "version": version
            }

    except Exception as error:
        return {
            "success": False,
            "message": str(error)
        }
