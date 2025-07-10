# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Renamed to avoid conflict
from typing import Generator

from backend.app.main import app # Main FastAPI app
from backend.app.models import Base, User, UserRole # Import Base and User for DB setup/teardown
from backend.db.session import get_db # Dependency to override
from backend.core.config import settings
from backend.core.security import get_password_hash

# Use a separate test database (e.g., SQLite in-memory for speed, or a test PostgreSQL DB)
# For simplicity here, using SQLite in-memory.
# Ensure your models are compatible if you switch between DB types often.
# SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test.db"
# If using a separate test PostgreSQL DB:
# SQLALCHEMY_DATABASE_URL_TEST = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/test_{settings.POSTGRES_DB}"
# For this example, let's use SQLite in-memory.
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    connect_args={"check_same_thread": False} # Needed for SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test database before tests run
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after tests are done (optional, as in-memory DB is ephemeral)
    # Base.metadata.drop_all(bind=engine) # Not strictly necessary for :memory:

@pytest.fixture(scope="function")
def db_session() -> Generator[SQLAlchemySession, None, None]:
    """
    Fixture to provide a database session for each test function.
    Rolls back transactions after each test to ensure isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_client(db_session: SQLAlchemySession) -> Generator[TestClient, None, None]:
    """
    Fixture to provide a FastAPI TestClient with overridden DB dependency.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            # db_session.close() # Session is managed by db_session fixture
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    del app.dependency_overrides[get_db] # Clean up override


# Utility fixture to create a test user directly in the DB
@pytest.fixture(scope="function")
def test_user(db_session: SQLAlchemySession) -> User:
    user_data = {
        "email": "testuser@example.com",
        "password_hash": get_password_hash("testpassword"),
        "role": UserRole.CLIENT,
        "is_active": True,
        "is_verified_email": True,
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_admin_user(db_session: SQLAlchemySession) -> User:
    user_data = {
        "email": "admin@example.com",
        "password_hash": get_password_hash("adminpassword"),
        "role": UserRole.ADMIN,
        "is_active": True,
        "is_verified_email": True,
    }
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
