# load the model and preprocessing objects
import os
import pickle
import numpy as np
import pandas as pd
from flask import current_app

# Global variables to store loaded components
_model = None
_scaler = None
_encoder = None
_categorical_cols = None
_continuous_cols = None
_feature_columns = None
_furnish_map = None

def load_model_components():
    """Load all model components once when app starts."""
    global _model, _scaler, _encoder, _categorical_cols, _continuous_cols, _feature_columns, _furnish_map
    
    if _model is not None:
        return  # Already loaded
    
    try:
        MODEL_DIR = current_app.config.get('MODEL_DIR', os.path.join(os.path.dirname(__file__), '..', 'Model'))
        
        print("Loading model components from:", MODEL_DIR)
        
        _model = pickle.load(open(os.path.join(MODEL_DIR, "best_model.pkl"), "rb"))
        _scaler = pickle.load(open(os.path.join(MODEL_DIR, "scaler.pkl"), "rb"))
        _encoder = pickle.load(open(os.path.join(MODEL_DIR, "encoder.pkl"), "rb"))
        _categorical_cols = pickle.load(open(os.path.join(MODEL_DIR, "categorical_cols.pkl"), "rb"))
        _continuous_cols = pickle.load(open(os.path.join(MODEL_DIR, "continuous_cols.pkl"), "rb"))
        _feature_columns = pickle.load(open(os.path.join(MODEL_DIR, "feature_columns.pkl"), "rb"))
        _furnish_map = pickle.load(open(os.path.join(MODEL_DIR, "furnish_map.pkl"), "rb"))
        
        print("✓ All model components loaded successfully!")
        
    except Exception as e:
        print(f"Error loading model components: {e}")
        raise

def preprocess_and_predict(input_data):
    """
    Preprocess input data and make prediction.
    
    Args:
        input_data (dict): Dictionary with keys:
            - Area_in_sqft (float)
            - Beds (int)
            - Baths (int)
            - Age_of_listing_in_days (int)
            - Furnishing (str): 'Furnished' or 'Unfurnished'
            - Type (str): Property type
            - Location (str): Location name
            - City (str): City name
    
    Returns:
        float: Predicted annual rent in AED
    """
    global _model, _scaler, _encoder, _categorical_cols, _continuous_cols, _feature_columns, _furnish_map
    
    # Ensure components are loaded
    if _model is None:
        load_model_components()
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame([input_data])
        
        # 1. Log transform area
        df["Log_Area"] = np.log1p(df["Area_in_sqft"])
        df.drop("Area_in_sqft", axis=1, inplace=True)
        
        # 2. Binary encode furnishing
        df["Furnishing"] = df["Furnishing"].map(_furnish_map).fillna(0).astype(float)
        
        # 3. One-hot encode categorical features
        df_encoded = _encoder.transform(df[_categorical_cols])
        encoded_cols = _encoder.get_feature_names_out(_categorical_cols)
        
        df.drop(_categorical_cols, axis=1, inplace=True)
        for i, col in enumerate(encoded_cols):
            df[col] = df_encoded[:, i]
        
        # 4. Scale continuous features
        df[_continuous_cols] = _scaler.transform(df[_continuous_cols])
        
        # 5. Ensure correct column order
        df = df[_feature_columns]
        
        # 6. Predict (log scale)
        prediction_log = _model.predict(df)[0]
        
        # 7. Convert back to original scale (AED)
        prediction_aed = float(np.exp(prediction_log))
        
        return prediction_aed
        
    except Exception as e:
        print(f"Error during prediction: {e}")
        raise