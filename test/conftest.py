import json
from datetime import datetime
from unittest.mock import patch

import pytest

from application import app, db
from application.models import User, Prediction


# ===========================================================
#  FIXTURES
# ===========================================================

@pytest.fixture
def app_fixture():
    """
    Create a fresh app + in-memory DB for each test run.
    Also disable CSRF so our form posts work in tests.
    """
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=False,   # keep login_required active
    )

    ctx = app.app_context()
    ctx.push()

    db.drop_all()
    db.create_all()

    yield app

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app_fixture):
    """
    Flask test client, depends on app_fixture so that context + DB exist.
    """
    return app_fixture.test_client()

