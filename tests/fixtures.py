""" shared fixtures """
import pytest
from falcon import testing
import service.microservice

CLIENT_HEADERS = {
    "ACCESS_KEY": "1234567"
}

BLUEBEAM_USERNAME = "user@sfgov.org"

@pytest.fixture()
def client():
    """ client fixture """
    return testing.TestClient(app=service.microservice.start_service(), headers=CLIENT_HEADERS)

@pytest.fixture
def mock_env_access_key(monkeypatch):
    """ mock environment access key """
    monkeypatch.setenv("ACCESS_KEY", CLIENT_HEADERS["ACCESS_KEY"])
    monkeypatch.setenv("BLUEBEAM_CLIENT_ID", "12345")
    monkeypatch.setenv("BLUEBEAM_CLIENT_SECRET", "12345")
    monkeypatch.setenv("BLUEBEAM_AUTHSERVER", "https://auth.test.com")
    monkeypatch.setenv("BLUEBEAM_USERNAME", BLUEBEAM_USERNAME)
    monkeypatch.setenv("BLUEBEAM_PASSWORD", "secret")
    monkeypatch.setenv("BLUEBEAM_API_BASE_URL", "https://api.test.com")
    monkeypatch.setenv("CLOUDSTORAGE_URL", "https://cloud.storage.com")
    monkeypatch.setenv("CLOUDSTORAGE_API_KEY", "12345")
    monkeypatch.setenv("BUCKETEER_DOMAIN", "bucketeer.com")
    monkeypatch.setenv("BUILDING_PERMITS_URL", "https://building.permits.com")
    monkeypatch.setenv("BUILDING_PERMITS_API_KEY", "apikey123")
    monkeypatch.setenv("BLUEBEAM_ACTION_STATE_VALUE", "Bluebeam Q")
    monkeypatch.setenv("ENCRYPTION_KEY", "ABCD1234")
    monkeypatch.setenv("CELERY_BEAT_SCHEDULE", "300")

@pytest.fixture
def mock_env_no_access_key(monkeypatch):
    """ mock environment with no access key """
    monkeypatch.delenv("ACCESS_KEY", raising=False)
