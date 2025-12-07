# UAE Rental Price Predictor

**By Chew Yee Jing (P2415860)**
**DAAA/FT/2A/21**

This project is a Flask-based machine learning web application that predicts rental prices across the United Arab Emirates (UAE). It integrates a trained machine learning model, a responsive web interface, a prediction history database, server-side filtering, and full deployment using Docker on Render.

This project is submitted for CA1 and demonstrates dataset preprocessing, model training, Flask backend development, HTML/WTForms UI, unit testing, Git version control, and deployment.

---

## 1. Project Overview

The UAE Rental Price Predictor allows users to estimate rental prices by selecting key property attributes such as city, location, bedrooms, bathrooms, furnishing type, and area. The application processes the inputs, loads a trained ML model, and returns an estimated rental price.

A prediction history page is included, featuring sorting, filtering (city, location, date range, rooms, area, etc.), and pagination. All predictions are stored in a SQLite database.

The full application is containerised using Docker and deployed later on.

---

## 2. Features

### Machine Learning

* Trained using a dataset of approximately 73,000+ UAE rental listings.
* Includes preprocessing with OneHotEncoder and StandardScaler.
* Log transformation applied to stabilise target distribution.
* Final model stored as `final_model_compressed_v2.joblib` after compressing the file to less than 100MB since github can only accept below 100MB.

### Web Application (Flask)

* Form-based prediction using WTForms.
* Clean and responsive UI built with Bootstrap and custom CSS.
* Prediction history stored in SQLite and displayed with filters and pagination.

### Deployment

* Dockerfile used for containerisation.
* Details regarding Deployment will be stated more in the slides.

### Testing

* Pytest test suite included.
* All 5 testing covered and also tested all the RESTFUL APIs used.
(Unexpected Failure Testing, Validity Testing, Consistency Testing, Expected Failure Testing, Range testing)
* 13 passing tests covering model loading, forms, routes, and database functions.

---

## 3. Machine Learning Model Details

* Log transformation applied:

```python
y_train_log = np.log(y_train)
```

* Categoricals encoded with OneHotEncoder.
* Numeric features scaled using StandardScaler.
* Trained several versions of the model to optimise memory usage for deployment.

I attempted to reduce the number of model parameters to fit Render’s 512 MB free-tier memory limit. However, this dropped model performance to approximately 70% accuracy. To avoid compromising prediction quality, I retained the stronger model, even though it occasionally triggers Render’s memory cap, which results in a 502 error. These attempts demonstrate my thought process for model selection and deployment constraints.

---

## 4. Folder Structure

```
├── application/
│   ├── __init__.py
│   ├── routes.py
│   ├── forms.py
│   ├── models.py
│   ├── predictor.py
│   ├── static/
│   │   └── css/style.css
│   ├── templates/
│       ├── layout.html
│       ├── index.html
│       ├── history.html
│       └── includes/
│
├── Model/
│   └── model.pkl
│
├── Dockerfile
├── requirements.txt
├── app.py
└── README.md
```

---

## 5. Running the Application Locally

### Step 1: Create Virtual Environment

```
python -m venv NEW_CA1_ENV
```

### Step 2: Activate Environment

Windows:

```
NEW_CA1_ENV\Scripts\activate
```

### Step 3: Install Dependencies

```
pip install -r requirements.txt
```

### Step 4: Start Flask Server

```
flask run
```

Local URL: `http://127.0.0.1:5000`

---

## 6. Deployment on Render

* Application is containerised using a custom Dockerfile.
* Render detects build and start commands automatically.
* Gunicorn serves the Flask application in production.
* Runs on assigned port 10000.

### Deployment Limitation

Render’s free tier provides only 512 MB RAM.
During heavy prediction tasks, the ML model and supporting libraries (pandas, scikit-learn) occasionally exceed this limit, which results in a 502 error. I explored downsizing the model and alternative platforms such as Heroku, but these also impose similar memory caps.

---

## 7. Branch Structure (SCRUM Workflow)

| Branch Name            | Purpose                                              |
| ---------------------- | ---------------------------------------------------- |
| branch1-ml-model       | Dataset preprocessing, training, exporting model.pkl |
| branch2-basic-setup    | Flask project setup, application structure           |
| branch3-prediction_ui  | WTForms prediction form and UI                       |
| branch4-prediction_api | Prediction API endpoint and model integration        |
| branch5-database       | Database setup, saving predictions, history page     |
| branch6-enhancement    | Filtering, sorting, pagination, improved CSS         |
| branch11-deployment    | Docker + Render deployment configuration             |

---

## 8. Testing

Run test suite:

```
python -m pytest
```

Expected output:

```
30 passed 
```

Tests cover:

* Form validation
* Flask route responses
* Prediction functionality
* Database integration

---

## 9. Future Enhancements

* Migrate to higher-memory hosting environment.
* Add interactive visualisations for trends.

---

## 10. Author

**Chew Yee Jing (P2415860)**
Diploma in Applied AI & Analytics
Singapore Polytechnic
DAAA/FT/2A/21

