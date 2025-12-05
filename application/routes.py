from application import app
from flask import render_template, request, flash
from application.forms import PredictionForm
from application.predictor import preprocess_and_predict



@app.route("/", methods=["GET", "POST"])
def index_page():
    form = PredictionForm()
    prediction = None

    if request.method == "POST" and form.validate_on_submit():

        # Build input dictionary
        input_data = {
            "Area_in_sqft": form.area_in_sqft.data,
            "Beds": form.beds.data,
            "Baths": form.baths.data,
            "Age_of_listing_in_days": form.age_of_listing_in_days.data,
            "Furnishing": form.furnishing.data,
            "Type": form.type.data,
            "Location": form.location.data,
            "City": form.city.data,
        }

        # Run model prediction
        try:
            prediction = preprocess_and_predict(input_data)
            flash(f"Predicted Annual Rent: {prediction:,.2f} AED", "success")
        except Exception as e:
            flash(f"Prediction error: {str(e)}", "danger")

    return render_template(
        "index.html",
        form=form,
        prediction=prediction
    )
