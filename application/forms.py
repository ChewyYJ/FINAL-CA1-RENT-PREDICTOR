from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import os
import pandas as pd

TOP_LOCATIONS = [
    "Al Reem Island",
    "Jumeirah Village Circle (JVC)",
    "Downtown Dubai",
    "Khalifa City",
    "Dubai Marina",
    "Mohammed Bin Zayed City",
    "Business Bay",
    "Muwailih Commercial",
    "Al Raha Beach",
    "Dubai Creek Harbour",
    "Meydan City",
    "Palm Jumeirah",
    "Muwailih",
    "Yas Island",
    "Dubai Hills Estate",

]

def get_location_choices():

    return sorted(TOP_LOCATIONS)


class PredictionForm(FlaskForm):
    area_in_sqft = FloatField(
        "Area (sqft)",
        validators=[
            DataRequired(message="Area is required"),
            NumberRange(min=300, max=70000, message="Area must be between 300 and 70,000 sqft")
        ]
    )
    beds = IntegerField(
        "Beds",
        validators=[
            DataRequired(message="Number of beds is required"),
            NumberRange(min=0, max=12, message="Beds must be between 0 and 12")
        ]
    )
    baths = IntegerField(
        "Baths",
        validators=[
            DataRequired(message="Number of baths is required"),
            NumberRange(min=0, max=10, message="Baths must be between 0 and 10")
        ]
    )
    age_of_listing_in_days = IntegerField(
        "Age of listing (days)",
        validators=[
            DataRequired(message="Age of listing is required"),
            NumberRange(min=0, max=3650, message="Age must be between 0 and 3,650 days")
        ]
    )
    furnishing = SelectField(
        "Furnishing",
        choices=[
            ("Furnished", "Furnished"), 
            ("Unfurnished", "Unfurnished")
        ],
        validators=[DataRequired()]
    )
    
    type = SelectField(
        "Property Type",
        choices=[
            ("Apartment", "Apartment"),
            ("Hotel Apartment", "Hotel Apartment"),
            ("Penthouse", "Penthouse"),
            ("Residential Building", "Residential Building"),
            ("Residential Floor", "Residential Floor"),
            ("Residential Plot", "Residential Plot"),
            ("Townhouse", "Townhouse"),
            ("Villa", "Villa"),
            ("Villa Compound", "Villa Compound"),
        ],
        validators=[DataRequired()]
    )
    
    location = StringField(
        "Location",
        validators=[DataRequired()]
    )
    
    city = SelectField(
        "City",
        choices=[
            ("Dubai", "Dubai"),
            ("Abu Dhabi", "Abu Dhabi"),
            ("Sharjah", "Sharjah"),
            ("Ajman", "Ajman"),
            ("Al Ain", "Al Ain"),
            ("Ras Al Khaimah", "Ras Al Khaimah"),
            ("Umm Al Quwain", "Umm Al Quwain"),
            ("Fujairah", "Fujairah"),
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Predict Rent")