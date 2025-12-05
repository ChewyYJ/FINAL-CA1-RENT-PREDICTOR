from application import app
from flask import render_template
from application.forms import PredictionForm

@app.route("/", methods=["GET", "POST"])
def index_page():
    form = PredictionForm()
    return render_template(
        "index.html",
        form=form,
        title="Enter Property Details"
    )
