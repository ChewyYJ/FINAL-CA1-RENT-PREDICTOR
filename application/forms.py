from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import os
import pandas as pd

def get_location_choices():
    try:
        # Get absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, 'Model', 'dubai_properties.csv')
        
        print(f"Loading CSV from: {csv_path}")
        df = pd.read_csv(csv_path)
        
        # Get top 50 most common locations
        top_locations = df['Location'].value_counts().head(50).index.tolist()
        print(f"Successfully loaded {len(top_locations)} locations!")
        
        return sorted(top_locations)  # Return list, not tuples
        
    except Exception as e:
        print("=" * 50)
        print("ERROR in get_location_choices:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("=" * 50)
        
        return [
            "Khalifa City, Abu Dhabi",
            "Mohammed Bin Zayed City, Abu Dhabi",
        ]
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