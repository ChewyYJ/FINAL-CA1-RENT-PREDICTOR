from application import app, db
from flask import render_template, request, flash, redirect, url_for, jsonify
from application.forms import PredictionForm, get_location_choices
# user auth
from application.models import User, Prediction
from application.predictor import preprocess_and_predict
from datetime import datetime
from application.forms import get_location_choices
# user auth imports 
from application.auth_forms import LoginForm, RegisterForm
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
# timezone handling
from datetime import datetime
import pytz

singapore_tz = pytz.timezone('Asia/Singapore')
created_at = datetime.now(singapore_tz)


@app.route("/")
@app.route("/index")
@app.route("/home")
def index_page():
    form = PredictionForm()
    locations = get_location_choices()

    # 1) Read page number from query string (?page=2 etc.)
    page = request.args.get("page", 1, type=int)
    per_page = 5    

    # 2) Base query (newest first)
    query = db.select(Prediction).order_by(Prediction.id.desc())
    
    # Onlt show current user's predictions if logged in
    if current_user.is_authenticated:
        query = query.where(Prediction.user_id == current_user.id)
    else:
        query = query.where(Prediction.user_id.is_(None))

    # 3) Paginate
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    entries = pagination.items

    # 4) True latest prediction (for big card + "Latest" badge)
    latest = db.session.execute(query.limit(1)).scalars().first()

    return render_template(
        "index.html",
        title="Enter Property Details",
        form=form,
        entries=entries,          
        pagination=pagination,    
        latest=latest,            
        locations=locations
    )




def add_entry(new_entry):
    try:
        db.session.add(new_entry)
        db.session.commit()
        return new_entry.id
    except Exception as error:
        db.session.rollback()
        flash(str(error), "danger")
        return None


def get_entries():
    try:
        query = db.select(Prediction).order_by(Prediction.id.desc())

        if current_user.is_authenticated:
            query = query.where(Prediction.user_id == current_user.id)

        entries = db.session.execute(query).scalars().all()
        return entries
    except Exception as error:
        db.session.rollback()
        flash(str(error), "danger")
        return []


def remove_entry(prediction_id):
    if not current_user.is_authenticated:
        return

    pred = Prediction.query.filter_by(
        id=prediction_id,
        user_id=current_user.id
    ).first()

    if pred:
        db.session.delete(pred)
        db.session.commit()
        flash("Prediction deleted successfully.", "success")
    else:
        flash("Prediction not found or does not belong to you.", "warning")


@app.route("/remove", methods=["POST"])
@login_required
def remove():
    prediction_id = request.form.get("id")
    source = request.form.get("source", "index")  # 'index' or 'history'

    if not prediction_id:
        flash("Unable to delete: missing prediction id.", "danger")
        if source == "history":
            return redirect(url_for("history"))
        return redirect(url_for("index_page", _anchor="history-card"))

    remove_entry(prediction_id)

    if source == "history":
        return redirect(url_for("history"))
    else:
        return redirect(url_for("index_page", _anchor="history-card"))


@app.route("/history")
@login_required
def history():
    form = PredictionForm()

    # ---------- query params ----------
    sort_by = request.args.get("sort_by", "created_at")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # ---------- ALL FILTERS ----------
    start_date_str = request.args.get("start_date", "")
    end_date_str   = request.args.get("end_date", "")
    city_filter        = request.args.get("city", "all")
    furnishing_filter  = request.args.get("furnishing", "all")
    type_filter        = request.args.get("property_type", "all")
    min_beds           = request.args.get("min_beds", type=int)
    max_beds           = request.args.get("max_beds", type=int)
    min_area           = request.args.get("min_area", type=int)
    max_area           = request.args.get("max_area", type=int)
    location_filter    = request.args.get('location', '')
    min_baths          = request.args.get('min_baths', type=int)
    max_baths          = request.args.get('max_baths', type=int)
    min_age            = request.args.get('min_age', type=int)
    max_age            = request.args.get('max_age', type=int)

    # DEBUG: Print all filter values
    print("=" * 50)
    print("FILTER VALUES:")
    print(f"city_filter: {city_filter}")
    print(f"furnishing_filter: {furnishing_filter}")
    print(f"type_filter: {type_filter}")
    print(f"location_filter: '{location_filter}'")
    print(f"min_beds: {min_beds}")
    print(f"max_beds: {max_beds}")
    print(f"min_baths: {min_baths}")
    print(f"max_baths: {max_baths}")
    print(f"min_area: {min_area}")
    print(f"max_area: {max_area}")
    print(f"min_age: {min_age}")
    print(f"max_age: {max_age}")
    print("=" * 50)

    # ---------- base query ----------
    query = db.select(Prediction)
    # limit to current user's predictions if logged in
    if current_user.is_authenticated:
        query = query.where(Prediction.user_id == current_user.id)
    else:
        query = query.where(Prediction.user_id.is_(None))
    # ---------- date range filter ----------
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            query = query.where(Prediction.created_at >= start_date)
            print(f"Applied start_date filter: {start_date}")

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.where(Prediction.created_at <= end_date)
            print(f"Applied end_date filter: {end_date}")
    except ValueError:
        flash("Invalid date format. Please use the date picker.", "warning")

    # ---------- ALL FIELD FILTERS ----------
    if city_filter and city_filter != "all":
        query = query.where(Prediction.city == city_filter)
        print(f"Applied city filter: {city_filter}")

    if furnishing_filter and furnishing_filter != "all":
        query = query.where(Prediction.furnishing == furnishing_filter)
        print(f"Applied furnishing filter: {furnishing_filter}")

    if type_filter and type_filter != "all":
        query = query.where(Prediction.property_type == type_filter)
        print(f"Applied type filter: {type_filter}")

    
    if location_filter and location_filter.strip():  
        query = query.where(Prediction.location.ilike(f'%{location_filter}%'))
        print(f"Applied location filter: {location_filter}")

    # Beds filter
    if min_beds is not None:
        query = query.where(Prediction.bedrooms >= min_beds)
        print(f"Applied min_beds filter: {min_beds}")
    if max_beds is not None:
        query = query.where(Prediction.bedrooms <= max_beds)
        print(f"Applied max_beds filter: {max_beds}")

    # Baths filter
    if min_baths is not None:
        query = query.where(Prediction.bathrooms >= min_baths)
        print(f"Applied min_baths filter: {min_baths}")
    if max_baths is not None:
        query = query.where(Prediction.bathrooms <= max_baths)
        print(f"Applied max_baths filter: {max_baths}")

    # Area filter
    if min_area is not None:
        query = query.where(Prediction.area >= min_area)
        print(f"Applied min_area filter: {min_area}")
    if max_area is not None:
        query = query.where(Prediction.area <= max_area)
        print(f"Applied max_area filter: {max_area}")

    # Age of listing filter
    if min_age is not None:
        query = query.where(Prediction.age_of_listing >= min_age)
        print(f"Applied min_age filter: {min_age}")
    if max_age is not None:
        query = query.where(Prediction.age_of_listing <= max_age)
        print(f"Applied max_age filter: {max_age}")

    # ---------- sorting ----------
    sort_map = {
        "created_at": Prediction.created_at,
        "rent":       Prediction.predicted_rent,
        "area":       Prediction.area,
        "beds":       Prediction.bedrooms,
        "city":       Prediction.city,
    }
    sort_col = sort_map.get(sort_by, Prediction.created_at)
    sort_expr = sort_col.asc() if order == "asc" else sort_col.desc()
    query = query.order_by(sort_expr)


    print(f"\nFinal query: {query}")
    
    # ---------- pagination ----------
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    entries = pagination.items
    

    print(f"Total items found: {pagination.total}")
    print(f"Items on this page: {len(entries)}")
    print("=" * 50)

    return render_template(
        "history.html",
        title="Prediction History",
        form=form,
        entries=entries,
        pagination=pagination,
        sort_by=sort_by,
        order=order,
        start_date=start_date_str,
        end_date=end_date_str,
        city_filter=city_filter,
        furnishing_filter=furnishing_filter,
        type_filter=type_filter,
        min_beds=min_beds,
        max_beds=max_beds,
        min_area=min_area,
        max_area=max_area,
        location_filter=location_filter,
        min_baths=min_baths,
        max_baths=max_baths,
        min_age=min_age,
        max_age=max_age
    )
    
# Routes for user registration and login 
@app.route("/predict", methods=["POST"])
def predict():
    form = PredictionForm()
    locations = get_location_choices()
    
    if form.validate_on_submit():
        # 1) Get data from form
        area = form.area_in_sqft.data
        beds = form.beds.data
        baths = form.baths.data
        age_days = form.age_of_listing_in_days.data
        furnishing = form.furnishing.data
        type_ = form.type.data
        location = form.location.data
        city = form.city.data

        # 2) Build input dict for model
        input_data = {
            "Area_in_sqft": area,
            "Beds": beds,
            "Baths": baths,
            "Age_of_listing_in_days": age_days,
            "Furnishing": furnishing,
            "Type": type_,
            "Location": location,
            "City": city,
        }

        try:
            # 3) Call ML pipeline
            predicted_rent = preprocess_and_predict(input_data)

            # 4) Get Singapore time
            singapore_tz = pytz.timezone('Asia/Singapore')
            created_at = datetime.now(singapore_tz)

            # 5) Save to DB
            new_entry = Prediction(
                area=area,
                bedrooms=beds,
                bathrooms=baths,
                furnishing=furnishing,
                age_of_listing=age_days,
                property_type=type_,
                city=city,
                location=location,
                predicted_rent=predicted_rent,
                created_at=created_at,
                user_id=current_user.id if current_user.is_authenticated else None
            )

            add_entry(new_entry)

            flash("Prediction successful!", "success")
            
            # Success: go to history
            return redirect(url_for("index_page", _anchor="history-card"))

        except Exception as error:
            db.session.rollback()
            flash(f"Error during prediction: {error}", "danger")
            # Error: stay at form
            return redirect(url_for("index_page", _anchor="predict-form"))
    else:
        # Display detailed validation errors
        if form.errors:
            for field, errors in form.errors.items():
                # Get user-friendly field names
                field_labels = {
                    'area_in_sqft': 'Area',
                    'beds': 'Beds',
                    'baths': 'Baths',
                    'age_of_listing_in_days': 'Age of listing',
                    'furnishing': 'Furnishing',
                    'type': 'Property Type',
                    'location': 'Location',
                    'city': 'City'
                }
                field_name = field_labels.get(field, field)
                
                for error in errors:
                    flash(f"{field_name}: {error}", "danger")
        else:
            flash("Error, cannot proceed with prediction", "danger")

    # Validation error: stay at form
    return redirect(url_for("index_page", _anchor="predict-form"))


@app.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, no need to register again
    if current_user.is_authenticated:
        return redirect(url_for("index_page"))

    form = RegisterForm()

    if form.validate_on_submit():
        # Check if username or email already exists
        existing_username = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()

        if existing_username:
            flash("Username is already taken. Please choose another.", "danger")
        elif existing_email:
            flash("Email is already registered. Please log in instead.", "danger")
        else:
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))

    return render_template("auth/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # look up by email
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Logged in successfully.", "success")
            

            next_page = request.args.get("next")
            return redirect(next_page or url_for("index_page"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index_page"))








# ==============================
# REST API ENDPOINTS (CA1 PART 3)
# ==============================

@app.route("/api/predictions", methods=["POST"])
def api_create_prediction():
    """
    REST API: Create a prediction.
    - Expects JSON body with:
      area, bedrooms, bathrooms, age_of_listing,
      furnishing, property_type, city, location
    - Calls ML model to get predicted_rent
    - Saves to DB and returns JSON
    """
    data = request.get_json(silent=True) or {}

    required_fields = [
        "area",
        "bedrooms",
        "bathrooms",
        "age_of_listing",
        "furnishing",
        "property_type",
        "city",
        "location",
    ]

    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({
            "success": False,
            "message": "Missing fields: " + ", ".join(missing)
        }), 400

    try:
        # basic type conversion
        area = float(data["area"])
        bedrooms = int(data["bedrooms"])
        bathrooms = int(data["bathrooms"])
        age_of_listing = int(data["age_of_listing"])
        furnishing = data["furnishing"]
        property_type = data["property_type"]
        city = data["city"]
        location = data["location"]

        # ========== Prepare input for ML model ==========
        input_data = {
            "Area_in_sqft": area,
            "Beds": bedrooms,
            "Baths": bathrooms,
            "Age_of_listing_in_days": age_of_listing,
            "Furnishing": furnishing,
            "Type": property_type,
            "Location": location,
            "City": city,
        }

        # Call ML pipeline
        predicted_rent = preprocess_and_predict(input_data)

        # Current time in Singapore
        singapore_tz = pytz.timezone("Asia/Singapore")
        created_at = datetime.now(singapore_tz)

        # Save to DB
        new_pred = Prediction(
            area=area,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            furnishing=furnishing,
            age_of_listing=age_of_listing,
            property_type=property_type,
            city=city,
            location=location,
            predicted_rent=predicted_rent,
            created_at=created_at,
            user_id=current_user.id if current_user.is_authenticated else None,
        )

        db.session.add(new_pred)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Prediction created successfully",
            "id": new_pred.id,
            "predicted_rent": float(predicted_rent),
            "currency": "AED",
            "created_at": created_at.isoformat()
        }), 200

    except (ValueError, TypeError) as e:
        return jsonify({
            "success": False,
            "message": f"Invalid input values: {e}"
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Unexpected server error: {e}"
        }), 500


@app.route("/api/predictions/<int:prediction_id>", methods=["GET"])
def api_get_prediction(prediction_id):
    """
    REST API: Get a single prediction by id.
    """
    pred = Prediction.query.get(prediction_id)
    if not pred:
        return jsonify({
            "success": False,
            "message": "Prediction not found"
        }), 404

    return jsonify({
        "success": True,
        "item": {
            "id": pred.id,
            "area": pred.area,
            "bedrooms": pred.bedrooms,
            "bathrooms": pred.bathrooms,
            "furnishing": pred.furnishing,
            "age_of_listing": pred.age_of_listing,
            "property_type": pred.property_type,
            "city": pred.city,
            "location": pred.location,
            "predicted_rent": float(pred.predicted_rent),
            "created_at": pred.created_at.isoformat() if pred.created_at else None,
        }
    }), 200


@app.route("/api/predictions/<int:prediction_id>", methods=["DELETE"])
def api_delete_prediction(prediction_id):
    """
    REST API: Delete a prediction by id.
    Uses HTTP DELETE method (correct REST style).
    """
    pred = Prediction.query.get(prediction_id)
    if not pred:
        return jsonify({
            "success": False,
            "message": "Prediction not found"
        }), 404

    try:
        db.session.delete(pred)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Prediction deleted successfully",
            "id": prediction_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Error deleting prediction: {e}"
        }), 500
