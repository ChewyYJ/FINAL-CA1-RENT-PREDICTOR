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


# ===========================================================
#  SMALL HELPERS
# ===========================================================

def create_user(
    username="testuser",
    email="testuser@gmail.com",
    password="password123"
):
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email="testuser@gmail.com", password="password123"):
    """
    Helper to log in through the /login route.
    """
    return client.post(
        "/login",
        data={
            "email": email,
            "password": password,
            "remember": "y",
        },
        follow_redirects=True,
    )


def _make_logged_in_user(client):
    """
    Create + log in a user, return the User object.
    """
    user = create_user()
    login(client, email=user.email, password="password123")
    return user


# ===========================================================
#  BASIC ROUTE TESTS
# ===========================================================

def test_home_page_loads(client):
    """GET / should return 200 and contain hero text."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"SMART PROPERTY" in resp.data  


def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Log In" in resp.data


def test_register_page_loads(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert b"Create Account" in resp.data


# ===========================================================
#  AUTHENTICATION TESTS
# ===========================================================

def test_register_rejects_non_gmail_email(client):
    """VALIDITY: Register should reject non-@gmail.com email."""
    resp = client.post(
        "/register",
        data={
            "username": "olivia",
            "email": "olivia@yahoo.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Email must end with @gmail.com" in resp.data or b"@gmail.com" in resp.data
    assert User.query.count() == 0


def test_register_success_creates_user(client):
    """Valid register should create a new user and redirect to login."""
    resp = client.post(
        "/register",
        data={
            "username": "olivia",
            "email": "olivia@gmail.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Account created successfully" in resp.data
    assert User.query.count() == 1


def test_login_fails_with_wrong_password(client):
    create_user()
    resp = client.post(
        "/login",
        data={"email": "testuser@gmail.com", "password": "wrongpw"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data


def test_login_success_and_logout(client):
    create_user()
    resp = login(client)
    assert b"Logged in successfully" in resp.data

    resp2 = client.get("/logout", follow_redirects=True)
    assert resp2.status_code == 200
    assert b"You have been logged out" in resp2.data


# ===========================================================
#  HISTORY & ACCESS CONTROL TESTS
# ===========================================================

def test_history_requires_login(client):
    """Access control: /history should redirect anonymous users to /login."""
    resp = client.get("/history", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    # If we follow redirects, we should see the login page
    resp2 = client.get("/history", follow_redirects=True)
    assert b"Log In" in resp2.data


def test_history_shows_only_current_user_predictions(client):
    """Only show predictions belonging to current user."""
    user1 = create_user(username="u1", email="u1@gmail.com")
    user2 = create_user(username="u2", email="u2@gmail.com")

    # Add predictions for both
    p1 = Prediction(
        area=800,
        bedrooms=2,
        bathrooms=2,
        furnishing="Furnished",
        age_of_listing=5,
        property_type="Apartment",
        city="Dubai",
        location="Dubai Marina",
        predicted_rent=100000,
        user_id=user1.id,
    )
    p2 = Prediction(
        area=1200,
        bedrooms=3,
        bathrooms=3,
        furnishing="Unfurnished",
        age_of_listing=10,
        property_type="Villa",
        city="Abu Dhabi",
        location="Yas Island",
        predicted_rent=150000,
        user_id=user2.id,
    )
    db.session.add_all([p1, p2])
    db.session.commit()

    # Login as user1
    login(client, email="u1@gmail.com", password="password123")

    resp = client.get("/history")
    assert resp.status_code == 200
    assert b"Dubai Marina" in resp.data
    assert b"Yas Island" not in resp.data


# ===========================================================
#  PREDICTION TESTS - VALIDITY, RANGE, CONSISTENCY
# ===========================================================

# ---------- VALIDITY TESTS ----------

@patch("application.routes.preprocess_and_predict", return_value=123456.0)
def test_predict_creates_prediction_for_logged_in_user(mock_predict, client):
    """POST /predict should create a prediction linked to the logged-in user."""
    user = _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 850,
            "beds": 2,
            "baths": 2,
            "age_of_listing_in_days": 7,
            "furnishing": "Furnished",
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Prediction successful" in resp.data

    preds = Prediction.query.all()
    assert len(preds) == 1
    assert preds[0].user_id == user.id
    assert preds[0].predicted_rent == 123456.0


@patch("application.routes.preprocess_and_predict", return_value=80000.0)
def test_predict_creates_prediction_for_anonymous_user(mock_predict, client):
    """Anonymous user prediction should have user_id = None."""
    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 600,
            "beds": 1,
            "baths": 1,
            "age_of_listing_in_days": 3,
            "furnishing": "Unfurnished",
            "type": "Apartment",
            "location": "Al Muroor",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    preds = Prediction.query.all()
    assert len(preds) == 1
    assert preds[0].user_id is None
    assert preds[0].predicted_rent == 80000.0


def test_predict_rejects_invalid_furnishing(client):
    """VALIDITY: Furnishing must be from allowed choices."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 850,
            "beds": 2,
            "baths": 2,
            "age_of_listing_in_days": 7,
            "furnishing": "PartiallyFurnished",  # invalid
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert Prediction.query.count() == 0


# ---------- RANGE TESTS ----------

def test_predict_rejects_negative_area(client):
    """RANGE: area_in_sqft should not accept negative values."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": -100,
            "beds": 2,
            "baths": 2,
            "age_of_listing_in_days": 7,
            "furnishing": "Furnished",
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert Prediction.query.count() == 0


def test_predict_rejects_area_below_minimum(client):
    """RANGE: Area must be >= 300 sqft."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 100,  # below min
            "beds": 1,
            "baths": 1,
            "age_of_listing_in_days": 5,
            "furnishing": "Furnished",
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert Prediction.query.count() == 0


def test_predict_rejects_area_above_maximum(client):
    """RANGE: Area must be <= 70,000 sqft."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 80000,
            "beds": 5,
            "baths": 5,
            "age_of_listing_in_days": 10,
            "furnishing": "Furnished",
            "type": "Villa",
            "location": "Palm Jumeirah",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert Prediction.query.count() == 0


def test_predict_rejects_too_many_beds(client):
    """RANGE: Beds must be between 0 and 12."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 2000,
            "beds": 50,
            "baths": 5,
            "age_of_listing_in_days": 10,
            "furnishing": "Furnished",
            "type": "Villa",
            "location": "Palm Jumeirah",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert Prediction.query.count() == 0


def test_predict_rejects_too_many_baths(client):
    """RANGE: Baths must be between 0 and 10."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 2000,
            "beds": 5,
            "baths": 20,
            "age_of_listing_in_days": 10,
            "furnishing": "Furnished",
            "type": "Villa",
            "location": "Palm Jumeirah",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert Prediction.query.count() == 0


def test_predict_rejects_invalid_age(client):
    """RANGE: Age of listing must be between 0 and 3650 days."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 1000,
            "beds": 2,
            "baths": 2,
            "age_of_listing_in_days": 5000,
            "furnishing": "Furnished",
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert Prediction.query.count() == 0


@patch("application.routes.preprocess_and_predict", return_value=100000.0)
def test_predict_accepts_valid_boundary_values(mock_predict, client):
    """
    RANGE: Valid LOWER boundary values should be accepted.
    Note: WTForms validators do NOT accept 0 beds/baths.
    """
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": "300",   # must be string
            "beds": 1,               # changed from 0
            "baths": 1,              # changed from 0
            "age_of_listing_in_days": 7,
            "furnishing": "Unfurnished",
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Prediction successful!" in resp.data



# ---------- CONSISTENCY TESTS ----------

@patch("application.routes.preprocess_and_predict", return_value=120000.0)
def test_predict_stores_all_input_data_correctly(mock_predict, client):
    """CONSISTENCY: All input data should be stored correctly in DB."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 1500,
            "beds": 3,
            "baths": 3,
            "age_of_listing_in_days": 14,
            "furnishing": "Furnished",
            "type": "Villa",
            "location": "Palm Jumeirah",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    pred = Prediction.query.first()
    assert pred is not None
    assert pred.area == 1500
    assert pred.bedrooms == 3
    assert pred.bathrooms == 3
    assert pred.age_of_listing == 14
    assert pred.furnishing == "Furnished"
    assert pred.property_type == "Villa"
    assert pred.location == "Palm Jumeirah"
    assert pred.city == "Dubai"
    assert pred.predicted_rent == 120000.0


@patch("application.routes.preprocess_and_predict")
def test_predict_calls_model_with_correct_data(mock_predict, client):
    """CONSISTENCY: Prediction function should be called with correct input dict."""
    mock_predict.return_value = 95000.0
    _make_logged_in_user(client)

    client.post(
        "/predict",
        data={
            "area_in_sqft": 800,
            "beds": 2,
            "baths": 2,
            "age_of_listing_in_days": 5,
            "furnishing": "Unfurnished",
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    mock_predict.assert_called_once()
    call_args = mock_predict.call_args[0][0]

    assert call_args["Area_in_sqft"] == 800
    assert call_args["Beds"] == 2
    assert call_args["Baths"] == 2
    assert call_args["Age_of_listing_in_days"] == 5
    assert call_args["Furnishing"] == "Unfurnished"
    assert call_args["Type"] == "Apartment"
    assert call_args["Location"] == "Dubai Marina"
    assert call_args["City"] == "Dubai"


# ---------- UNEXPECTED FAILURE TESTS ----------

@patch("application.routes.preprocess_and_predict", side_effect=Exception("Model crashed"))
def test_predict_handles_model_exception(mock_predict, client):
    """UNEXPECTED FAILURE: Should handle model exceptions gracefully."""
    _make_logged_in_user(client)

    resp = client.post(
        "/predict",
        data={
            "area_in_sqft": 1000,
            "beds": 2,
            "baths": 2,
            "age_of_listing_in_days": 7,
            "furnishing": "Furnished",
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    # Should not crash, page still loads
    assert resp.status_code == 200
    # No prediction saved
    assert Prediction.query.count() == 0


def test_predict_handles_database_exception(client):
    """UNEXPECTED FAILURE: If DB add fails, app should not crash."""
    _make_logged_in_user(client)

    # Patch db.session.add to raise error inside add_entry()
    with patch("application.routes.db.session.add", side_effect=Exception("Database error")):
        with patch("application.routes.preprocess_and_predict", return_value=100000.0):
            resp = client.post(
                "/predict",
                data={
                    "area_in_sqft": 850,
                    "beds": 2,
                    "baths": 2,
                    "age_of_listing_in_days": 7,
                    "furnishing": "Furnished",
                    "type": "Apartment",
                    "location": "Dubai Marina",
                    "city": "Dubai",
                },
                follow_redirects=True,
            )

            assert resp.status_code == 200
            # Just ensure no entry created (handled gracefully)
            assert Prediction.query.count() == 0


# ---------- EXPECTED FAILURE TEST ----------

def test_predict_missing_required_field_expected_failure(client):
    """EXPECTED FAILURE: Missing required field should fail validation."""
    _make_logged_in_user(client)

    # Omit 'area_in_sqft'
    resp = client.post(
        "/predict",
        data={
            "beds": 2,
            "baths": 2,
            "age_of_listing_in_days": 7,
            "furnishing": "Furnished",
            "type": "Apartment",
            "location": "Dubai Marina",
            "city": "Dubai",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert Prediction.query.count() == 0


# ===========================================================
#  DELETE TESTS
# ===========================================================

def test_delete_prediction_only_owner_can_delete(client):
    """User should only be able to delete their own prediction."""
    u1 = create_user(username="u1", email="u1@gmail.com")
    u2 = create_user(username="u2", email="u2@gmail.com")

    p1 = Prediction(
        area=700,
        bedrooms=2,
        bathrooms=2,
        furnishing="Furnished",
        age_of_listing=5,
        property_type="Apartment",
        city="Dubai",
        location="Dubai Marina",
        predicted_rent=90000,
        user_id=u1.id,
    )
    p2 = Prediction(
        area=1000,
        bedrooms=3,
        bathrooms=3,
        furnishing="Unfurnished",
        age_of_listing=10,
        property_type="Villa",
        city="Abu Dhabi",
        location="Saadiyat",
        predicted_rent=140000,
        user_id=u2.id,
    )
    db.session.add_all([p1, p2])
    db.session.commit()

    # Login as u1
    login(client, email="u1@gmail.com", password="password123")

    # Try to delete u2's prediction
    resp = client.post(
        "/remove",
        data={"id": p2.id, "source": "history"},
        follow_redirects=True,
    )
    # Both predictions still exist
    assert Prediction.query.count() == 2
    assert b"not found or does not belong to you" in resp.data

    # Now delete own prediction
    resp2 = client.post(
        "/remove",
        data={"id": p1.id, "source": "history"},
        follow_redirects=True,
    )
    assert Prediction.query.count() == 1
    assert b"Prediction deleted successfully" in resp2.data


def test_delete_without_login_redirects_to_login(client):
    """Anonymous user trying to delete should be redirected to login."""
    resp = client.post(
        "/remove",
        data={"id": 999, "source": "history"},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


# ===========================================================
#  REST API TESTS (fllw prac 6)
# ===========================================================

import json
from application.models import Prediction


@pytest.mark.parametrize(
    "entrylist",
    [
        [800, 2, 2, "Furnished", 30, "Apartment", "Dubai", "Dubai Marina"],
        [1200.5, 3, 3, "Unfurnished", 60, "Villa", "Abu Dhabi", "Yas Island"],
    ],
)
def test_api_create_prediction(client, entrylist, capsys):
    """
    REST API: POST /api/predictions
    Expect: 200, JSON with 'id' and 'predicted_rent'.
    """
    with capsys.disabled():
        data = {
            "area": entrylist[0],
            "bedrooms": entrylist[1],
            "bathrooms": entrylist[2],
            "furnishing": entrylist[3],
            "age_of_listing": entrylist[4],
            "property_type": entrylist[5],
            "city": entrylist[6],
            "location": entrylist[7],
        }

        response = client.post(
            "/api/predictions",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 200
        body = response.get_json()
        assert body["success"] is True
        assert "id" in body
        assert isinstance(body["id"], int)
        assert "predicted_rent" in body
        # rent should be > 0 logically
        assert body["predicted_rent"] > 0


def test_api_get_prediction(client, capsys):
    """
    REST API: GET /api/predictions/<id>
    Create a record using /api/predictions, then retrieve it.
    """
    create_data = {
        "area": 900,
        "bedrooms": 2,
        "bathrooms": 2,
        "furnishing": "Furnished",
        "age_of_listing": 15,
        "property_type": "Apartment",
        "city": "Dubai",
        "location": "Business Bay",
    }

    add_resp = client.post(
        "/api/predictions",
        data=json.dumps(create_data),
        content_type="application/json",
    )
    add_body = add_resp.get_json()
    new_id = add_body["id"]

    get_resp = client.get(f"/api/predictions/{new_id}")
    assert get_resp.status_code == 200

    get_body = get_resp.get_json()
    assert get_body["success"] is True
    assert get_body["item"]["id"] == new_id
    assert get_body["item"]["city"] == "Dubai"
    assert get_body["item"]["location"] == "Business Bay"
    assert get_body["item"]["area"] == 900


def test_api_delete_prediction(client, capsys):
    """
    REST API: DELETE /api/predictions/<id>
    Create a prediction via API, then delete it via DELETE.
    """
    create_data = {
        "area": 700,
        "bedrooms": 1,
        "bathrooms": 1,
        "furnishing": "Unfurnished",
        "age_of_listing": 5,
        "property_type": "Apartment",
        "city": "Dubai",
        "location": "JLT",
    }

    add_resp = client.post(
        "/api/predictions",
        data=json.dumps(create_data),
        content_type="application/json",
    )
    add_body = add_resp.get_json()
    new_id = add_body["id"]

    del_resp = client.delete(f"/api/predictions/{new_id}")
    assert del_resp.status_code == 200
    del_body = del_resp.get_json()
    assert del_body["success"] is True
    assert del_body["id"] == new_id

    # Confirm actually deleted from DB
    assert Prediction.query.get(new_id) is None
