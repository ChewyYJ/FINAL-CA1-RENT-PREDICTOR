from application import app, db
from flask import render_template, request, flash, redirect, url_for
from application.forms import PredictionForm, get_location_choices
from application.models import Prediction
from application.predictor import preprocess_and_predict
from datetime import datetime
from application.forms import get_location_choices



@app.route("/")
@app.route("/index")
@app.route("/home")
def index_page():
    form = PredictionForm()
    locations = get_location_choices()

    # 1) Read page number from query string (?page=2 etc.)
    page = request.args.get("page", 1, type=int)
    per_page = 5   # or 10 if you prefer

    # 2) Base query (newest first)
    query = db.select(Prediction).order_by(Prediction.id.desc())

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

            # 4) Save to DB
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
                created_at=datetime.utcnow(),
            )

            add_entry(new_entry)

            # Flash message to trigger toast notification
            flash("prediction_success", "success")

        except Exception as error:
            db.session.rollback()
            flash(f"Error during prediction: {error}", "danger")
    else:
        flash("Error, cannot proceed with prediction", "danger")

    return redirect(url_for("index_page", _anchor="history-card"))


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
        entries = db.session.execute(
            db.select(Prediction).order_by(Prediction.id.desc())
        ).scalars().all()
        return entries
    except Exception as error:
        db.session.rollback()
        flash(str(error), "danger")
        return []

@app.route("/remove", methods=["POST"])
def remove():
    prediction_id = request.form.get("id")           
    source = request.form.get("source", "index")    

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


def remove_entry(id):
    try:
        entry = db.get_or_404(Prediction, id)
        db.session.delete(entry)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        flash(str(error), "danger")
        return 0



@app.route("/history")
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

    # Location filter (partial match) - BE CAREFUL WITH EMPTY STRINGS!
    if location_filter and location_filter.strip():  # Added .strip() check
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

    # DEBUG: Check query before pagination
    print(f"\nFinal query: {query}")
    
    # ---------- pagination ----------
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    entries = pagination.items
    
    # DEBUG: Check results
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