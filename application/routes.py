from application import app, db
from flask import render_template, request, flash, redirect, url_for
from application.forms import PredictionForm, get_location_choices
from application.models import Prediction
from application.predictor import preprocess_and_predict
from datetime import datetime
 


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
    form = PredictionForm()
    id = request.form["id"]
    remove_entry(id)
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

