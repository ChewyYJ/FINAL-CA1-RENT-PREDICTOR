from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class PredictionForm(FlaskForm):
    area_in_sqft = FloatField(
        "Area (sqft)",
        validators=[DataRequired(), NumberRange(min=100)]
    )
    beds = IntegerField(
        "Beds",
        validators=[DataRequired(), NumberRange(min=0)]
    )
    baths = IntegerField(
        "Baths",
        validators=[DataRequired(), NumberRange(min=0)]
    )
    age_of_listing_in_days = IntegerField(
        "Age of listing (days)",
        validators=[DataRequired(), NumberRange(min=0)]
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
    
    # Changed to StringField for type-ahead
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