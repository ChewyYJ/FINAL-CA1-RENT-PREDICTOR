# define a prediction table to store the model inputs and outputs

from application import db

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    area = db.Column(db.Float)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    furnishing = db.Column(db.String(15))
    age_of_listing = db.Column(db.Integer)
    property_type = db.Column(db.String(20))
    city = db.Column(db.String(50))
    location = db.Column(db.String(100))
    
    predicted_rent = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # for my debug - override the string representation method cos str returns memory addrress
    def __repr__(self):
        return f'<Prediction {self.id}: {self.predicted_value}>'