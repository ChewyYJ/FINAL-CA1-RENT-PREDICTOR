from application import app
from flask import render_template 

@app.route("/")
@app.route("/index")
@app.route("/home")
def index_page():
 
    return render_template(
        "index.html",
        title="Enter Property Details"
    )

@app.route("/predict", methods=["GET", "POST"])
def predict():
    pass

@app.route("/history")
def history():
    pass
