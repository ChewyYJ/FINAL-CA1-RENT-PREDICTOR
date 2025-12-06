# tests/conftest.py
import pytest

from application import app as flask_app, db
from application.models import Prediction, User


@pytest.fixture
def app():
    """
    Test version of the Flask app.

    - Uses an in-memory SQLite DB (does NOT touch your real DB file)
    - Disables CSRF so WTForms doesn't block POSTs
    - Disables login requirement so we can call routes easily
    """
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=True,      # flask-login: skip @login_required in tests
    )

    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Flask test client for making HTTP calls in tests.
    """
    return app.test_client()
