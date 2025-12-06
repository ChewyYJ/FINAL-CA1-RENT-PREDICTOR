# load the model and preprocessing objects
import os
import joblib
import lzma  # ← Added for decompression
import pickle  # ← Added for loading from lzma
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
        MODEL_DIR = current_app.config.get(
            'MODEL_DIR',
            os.path.join(os.path.dirname(__file__), '..', 'Model')
        )

        print("Loading model components from:", MODEL_DIR)

        # -------- Load compressed model with lzma --------
        model_path = os.path.join(MODEL_DIR, "best_model_compressed_lzma.pkl")  # ← Updated filename

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load compressed model
        print("Decompressing model (this may take a moment)...")
        with lzma.open(model_path, 'rb') as f:
            _model = pickle.load(f)
        print("✓ Loaded and decompressed model from:", model_path)
        
        # Load all other components with joblib (these aren't compressed)
        _scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        _encoder = joblib.load(os.path.join(MODEL_DIR, "encoder.pkl"))
        _categorical_cols = joblib.load(os.path.join(MODEL_DIR, "categorical_cols.pkl"))
        _continuous_cols = joblib.load(os.path.join(MODEL_DIR, "continuous_cols.pkl"))
        _feature_columns = joblib.load(os.path.join(MODEL_DIR, "feature_columns.pkl"))
        _furnish_map = joblib.load(os.path.join(MODEL_DIR, "furnish_map.pkl"))
        
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