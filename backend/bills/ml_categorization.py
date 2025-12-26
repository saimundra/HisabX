import pickle
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from django.conf import settings
from bills.models import Bill, Category
import logging

logger = logging.getLogger(__name__)

class MLBillCategorizer:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = {}
        self.reverse_label_encoder = {}
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'bill_categorizer.pkl')
        self.vectorizer_path = os.path.join(settings.BASE_DIR, 'ml_models', 'vectorizer.pkl')
        
        # Create ml_models directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Try to load existing model
        self.load_model()
    
    def prepare_features(self, bill):
        """Extract features from a bill for ML model"""
        features_text = []
        
        # Vendor name (most important)
        if bill.vendor:
            features_text.append(bill.vendor.lower())
        
        # OCR text
        if bill.ocr_text:
            features_text.append(bill.ocr_text.lower())
        
        # Invoice number patterns
        if bill.invoice_number:
            features_text.append(bill.invoice_number)
        
        # Amount-based features (as text for TF-IDF)
        if bill.amount:
            amount = float(bill.amount)
            if amount < 100:
                features_text.append("low_amount")
            elif amount < 1000:
                features_text.append("medium_amount")
            elif amount < 10000:
                features_text.append("high_amount")
            else:
                features_text.append("very_high_amount")
        
        return " ".join(features_text)
    
    def prepare_training_data(self):
        """Prepare training data from categorized bills"""
        # Get all manually categorized bills (high quality labels)
        bills = Bill.objects.filter(
            category__isnull=False,
            is_auto_categorized=False  # Only use manually categorized bills for training
        )
        
        if bills.count() < 10:
            logger.warning("Not enough manually categorized bills for training. Need at least 10.")
            return None, None
        
        X = []
        y = []
        
        # Build label encoder
        categories = Category.objects.all()
        self.label_encoder = {cat.name: idx for idx, cat in enumerate(categories)}
        self.reverse_label_encoder = {idx: cat.name for cat.name, idx in self.label_encoder.items()}
        
        for bill in bills:
            features = self.prepare_features(bill)
            X.append(features)
            y.append(self.label_encoder[bill.category.name])
        
        return X, y
    
    def train_model(self, test_size=0.2, random_state=42):
        """Train the ML model on categorized bills"""
        logger.info("Starting ML model training...")
        
        # Prepare data
        X, y = self.prepare_training_data()
        
        if X is None or len(X) < 10:
            logger.error("Insufficient training data. Need at least 10 categorized bills.")
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Vectorize text features
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),  # Use unigrams and bigrams
            min_df=1,
            max_df=0.9
        )
        
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Train Random Forest model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            class_weight='balanced'  # Handle class imbalance
        )
        
        self.model.fit(X_train_vec, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Model trained with accuracy: {accuracy:.2%}")
        logger.info("\nClassification Report:")
        logger.info(classification_report(
            y_test, y_pred,
            target_names=[self.reverse_label_encoder[i] for i in sorted(self.reverse_label_encoder.keys())]
        ))
        
        # Save model
        self.save_model()
        
        return True
    
    def predict_category(self, bill):
        """Predict category for a bill using ML model"""
        if self.model is None or self.vectorizer is None:
            logger.warning("ML model not loaded. Attempting to load...")
            if not self.load_model():
                return None, 0.0
        
        # Prepare features
        features = self.prepare_features(bill)
        features_vec = self.vectorizer.transform([features])
        
        # Predict
        prediction = self.model.predict(features_vec)[0]
        probabilities = self.model.predict_proba(features_vec)[0]
        
        # Get category name and confidence
        category_name = self.reverse_label_encoder[prediction]
        confidence = probabilities[prediction]
        
        # Get category object
        try:
            category = Category.objects.get(name=category_name)
            return category, confidence
        except Category.DoesNotExist:
            logger.error(f"Category '{category_name}' not found in database")
            return None, 0.0
    
    def save_model(self):
        """Save trained model and vectorizer to disk"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'label_encoder': self.label_encoder,
                    'reverse_label_encoder': self.reverse_label_encoder
                }, f)
            
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            logger.info(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self):
        """Load trained model and vectorizer from disk"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.label_encoder = data['label_encoder']
                    self.reverse_label_encoder = data['reverse_label_encoder']
                
                with open(self.vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                
                logger.info("ML model loaded successfully")
                return True
            else:
                logger.info("No trained model found")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def get_feature_importance(self, top_n=20):
        """Get most important features for categorization"""
        if self.model is None or self.vectorizer is None:
            return None
        
        feature_names = self.vectorizer.get_feature_names_out()
        importances = self.model.feature_importances_
        
        # Get top N features
        indices = np.argsort(importances)[-top_n:]
        top_features = [(feature_names[i], importances[i]) for i in indices]
        
        return sorted(top_features, key=lambda x: x[1], reverse=True)
aqQA