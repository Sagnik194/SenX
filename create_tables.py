
from database.connection import engine, Base
from database import models


def create_tables():
    print("Creating SenX database tables...")

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()
