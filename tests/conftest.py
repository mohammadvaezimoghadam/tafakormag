import os
import pytest
import django

# Initialize Django environment variables and configurations
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "note_platform.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Monkeypatch Django to prevent it from renaming the database (prepending 'test_') 
# when running Django TestCase instances, ensuring it shares the DB with the backend container.
from django.db.backends.base.creation import BaseDatabaseCreation
BaseDatabaseCreation._get_test_db_name = lambda self: self.connection.settings_dict['NAME']

django.setup()

@pytest.fixture(scope="session")
def backend_url():
    """Returns the internal Docker network URL of the Django backend container."""
    return os.getenv("BACKEND_URL", "http://backend:8000")

@pytest.fixture(scope="session")
def frontend_url():
    """Returns the internal Docker network URL of the Vue frontend container."""
    return os.getenv("FRONTEND_URL", "http://vue-frontend:80")

@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """
    Overrides the default django_db_setup.
    Since we connect to a shared, ephemeral PostgreSQL container which has
    already been migrated by the backend container on startup, we
    just unblock the connection and reuse the active database.
    """
    with django_db_blocker.unblock():
        pass

@pytest.fixture(autouse=True)
def clean_db(django_db_blocker):
    """
    Wipes the database tables clean before each test to ensure complete isolation.
    Using 'flush' keeps the schema intact, but deletes all database rows.
    """
    with django_db_blocker.unblock():
        from django.core.management import call_command
        # Wipes all tables, resets auto-increment sequences, runs without prompt
        call_command("flush", interactive=False, reset_sequences=True)

@pytest.fixture
def browser_context_args(browser_context_args, frontend_url):
    """
    Overrides Playwright context arguments.
    Sets the base URL to our Vue frontend service inside the Docker network,
    configures standard viewport size, and ignores self-signed certificates.
    """
    return {
        **browser_context_args,
        "base_url": frontend_url,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Capture screenshots of the browser page on E2E test failures
    and write them to the mounted volume directory on the host machine.
    """
    outcome = yield
    rep = outcome.get_result()
    
    # We only care if the test execution fails (excludes setup/teardown failures)
    if rep.when == "call" and rep.failed:
        # Check if the test has a playwright 'page' fixture
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            artifacts_dir = "/app/tests/artifacts"
            os.makedirs(artifacts_dir, exist_ok=True)
            
            # Formulate a safe filename
            safe_nodeid = item.nodeid.replace("/", "_").replace(":", "_").replace(".py", "")
            screenshot_path = f"{artifacts_dir}/{safe_nodeid}.png"
            
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"\n[Playwright Failure] Saved screenshot to: {screenshot_path}")
            except Exception as e:
                print(f"Failed to capture screenshot: {e}")
