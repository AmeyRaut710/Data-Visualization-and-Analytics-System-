import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_squared_error, accuracy_score, f1_score
from xgboost import XGBRegressor, XGBClassifier
import shap
import json

class PredictionAgent:
    def predict(self, df: pd.DataFrame, target_column: str) -> dict:
        if target_column not in df.columns:
            return {"error": "Target column not found in dataset."}
            
        # Drop rows where target is missing
        df_clean = df.dropna(subset=[target_column]).copy()
        
        if len(df_clean) < 50:
            return {"error": "Not enough data for prediction. Need at least 50 valid rows."}
            
        y = df_clean[target_column]
        X = df_clean.drop(columns=[target_column])
        
        # Identify task type
        is_classification = False
        if pd.api.types.is_object_dtype(y) or isinstance(y.dtype, pd.CategoricalDtype) or len(y.unique()) < 20:
            is_classification = True
            
        # Preprocessing X
        X = X.dropna(axis=1, thresh=int(0.5 * len(X)))
        
        numerical_cols = X.select_dtypes(include=['number']).columns
        categorical_cols = X.select_dtypes(include=['object', 'category', 'bool']).columns
        
        X[numerical_cols] = X[numerical_cols].fillna(X[numerical_cols].median())
        for col in categorical_cols:
            X[col] = X[col].fillna(X[col].mode()[0] if not X[col].mode().empty else "Unknown")
            
        # Encode categoricals
        label_encoders = {}
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
            
        if is_classification:
            le_y = LabelEncoder()
            y = le_y.fit_transform(y.astype(str))
            
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        if is_classification:
            model = XGBClassifier(random_state=42)
        else:
            model = XGBRegressor(random_state=42)
            
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Metrics
        metrics = {}
        if is_classification:
            metrics["accuracy"] = float(accuracy_score(y_test, y_pred))
            metrics["f1_score"] = float(f1_score(y_test, y_pred, average='weighted'))
        else:
            metrics["r2_score"] = float(r2_score(y_test, y_pred))
            metrics["rmse"] = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            
        # SHAP values
        explainer = shap.TreeExplainer(model)
        sample_size = min(100, len(X_train))
        X_sample = shap.sample(X_train, sample_size)
        shap_values = explainer.shap_values(X_sample)
        
        if isinstance(shap_values, list): # Multi-class
            shap_sum = np.abs(shap_values[0]).mean(axis=0)
        else:
            shap_sum = np.abs(shap_values).mean(axis=0)
            
        importance_df = pd.DataFrame([X.columns.tolist(), shap_sum.tolist()]).T
        importance_df.columns = ['feature', 'importance']
        importance_df['importance'] = importance_df['importance'].astype(float)
        importance_df = importance_df.sort_values('importance', ascending=False).head(10)
        
        return {
            "task_type": "Classification" if is_classification else "Regression",
            "metrics": metrics,
            "feature_importance": importance_df.to_dict(orient='records')
        }
