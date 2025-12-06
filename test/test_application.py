# test_app.py
import unittest
from unittest.mock import patch

from application import app, db
from application.models import User, Prediction


class BaseTestCase(unittest.TestCase):
    """Base class: config test client + clean DB for every test."""

    def setUp(self):
        # Test configuration
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False  # disable CSRF for form posts

        self.app = app
        self.client = self.app.test_client()

        # Push app context & reset DB
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # ------- small helpers -------

    def create_user(self, username="testuser", email="testuser@gmail.com",
                    password="password123"):
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, email="testuser@gmail.com", password="password123"):
        """Helper to log in a user using the /login route."""
        return self.client.post(
            "/login",
            data={
                "email": email,
                "password": password,
                "remember": "y",
            },
            follow_redirects=True,
        )


# ===========================================================
#  BASIC ROUTE TESTS
# ===========================================================
class BasicRouteTests(BaseTestCase):
    def test_home_page_loads(self):
        """GET / should return 200 and contain hero text."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"SMART PROPERTY", resp.data)

    def test_login_page_loads(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Log In", resp.data)

    def test_register_page_loads(self):
        resp = self.client.get("/register")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Create Account", resp.data)


# ===========================================================
#  AUTHENTICATION TESTS
# ===========================================================
class AuthTests(BaseTestCase):
    def test_register_rejects_non_gmail_email(self):
        """Register should reject non-@gmail.com email."""
        resp = self.client.post(
            "/register",
            data={
                "username": "olivia",
                "email": "olivia@yahoo.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Email must end with @gmail.com.", resp.data)
        self.assertEqual(User.query.count(), 0)

    def test_register_success_creates_user(self):
        """Valid register should create a new user and redirect to login."""
        resp = self.client.post(
            "/register",
            data={
                "username": "olivia",
                "email": "olivia@gmail.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Account created successfully! Please log in.", resp.data)
        self.assertEqual(User.query.count(), 1)

    def test_login_fails_with_wrong_password(self):
        self.create_user()
        resp = self.client.post(
            "/login",
            data={"email": "testuser@gmail.com", "password": "wrongpw"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid email or password.", resp.data)

    def test_login_success_and_logout(self):
        self.create_user()
        resp = self.login()
        self.assertIn(b"Logged in successfully.", resp.data)

        # Logout
        resp2 = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(resp2.status_code, 200)
        self.assertIn(b"You have been logged out.", resp2.data)


# ===========================================================
#  HISTORY & ACCESS CONTROL TESTS
# ===========================================================
class HistoryAndAccessTests(BaseTestCase):
    def test_history_requires_login(self):
        """Anonymous user should be redirected to login when visiting /history."""
        resp = self.client.get("/history", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

        # With follow_redirects=True, we land on login page
        resp2 = self.client.get("/history", follow_redirects=True)
        self.assertIn(b"Log In", resp2.data)

    def test_history_shows_only_current_user_predictions(self):
        """Only show predictions belonging to current user."""
        user1 = self.create_user(username="u1", email="u1@gmail.com")
        user2 = self.create_user(username="u2", email="u2@gmail.com")

        # Add predictions for both users
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
        self.login(email="u1@gmail.com")

        resp = self.client.get("/history")
        self.assertEqual(resp.status_code, 200)

        # Should see user1's prediction details
        self.assertIn(b"Dubai Marina", resp.data)
        # Should NOT see user2's prediction location
        self.assertNotIn(b"Yas Island", resp.data)


# ===========================================================
#  PREDICTION + DELETE TESTS
# ===========================================================
class PredictionTests(BaseTestCase):
    def _make_logged_in_user(self):
        user = self.create_user()
        self.login(email="testuser@gmail.com", password="password123")
        return user

    @patch("application.routes.preprocess_and_predict", return_value=123456.0)
    def test_predict_creates_prediction_for_logged_in_user(self, mock_predict):
        """POST /predict should create a prediction linked to the logged-in user."""
        user = self._make_logged_in_user()

        resp = self.client.post(
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

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Prediction successful!", resp.data)

        preds = Prediction.query.all()
        self.assertEqual(len(preds), 1)
        self.assertEqual(preds[0].user_id, user.id)
        self.assertEqual(preds[0].predicted_rent, 123456.0)

    @patch("application.routes.preprocess_and_predict", return_value=80000.0)
    def test_predict_creates_prediction_for_anonymous_user(self, mock_predict):
        """Anonymous user prediction should have user_id = None."""
        resp = self.client.post(
            "/predict",
            data={
                "area_in_sqft": 600,
                "beds": 1,
                "baths": 1,
                "age_of_listing_in_days": 3,
                "furnishing": "Unfurnished",
                "type": "Apartment",
                "location": "Sharjah City Center",
                "city": "Sharjah",
            },
            follow_redirects=True,
        )

        self.assertEqual(resp.status_code, 200)
        preds = Prediction.query.all()
        self.assertEqual(len(preds), 1)
        self.assertIsNone(preds[0].user_id)

    def test_predict_rejects_negative_area(self):
        """Range testing: area_in_sqft should not accept negative values."""
        self._make_logged_in_user()

        resp = self.client.post(
            "/predict",
            data={
                "area_in_sqft": -100,  # invalid range
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

        # Form should re-render, not crash, and no prediction created
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Prediction.query.count(), 0)
        # Optional: if you show a specific error, also check:
        # self.assertIn(b"Area must be", resp.data)

    def test_delete_prediction_only_owner_can_delete(self):
        """User should only be able to delete their own prediction."""
        # Create two users + one prediction each
        u1 = self.create_user(username="u1", email="u1@gmail.com")
        u2 = self.create_user(username="u2", email="u2@gmail.com")

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
        self.login(email="u1@gmail.com", password="password123")

        # Try to delete u2's prediction
        resp = self.client.post(
            "/remove",
            data={"id": p2.id, "source": "history"},
            follow_redirects=True,
        )

        # Both predictions should still exist
        self.assertEqual(Prediction.query.count(), 2)
        self.assertIn(b"not found or does not belong to you", resp.data)

        # Now delete own prediction
        resp2 = self.client.post(
            "/remove",
            data={"id": p1.id, "source": "history"},
            follow_redirects=True,
        )
        self.assertEqual(Prediction.query.count(), 1)
        self.assertIn(b"Prediction deleted successfully.", resp2.data)

if __name__ == "__main__":
    unittest.main()
