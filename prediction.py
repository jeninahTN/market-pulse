import numpy as np
import os
import pickle
import json
from pathlib import Path
import pandas as pd

class PredictionService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_path = Path(__file__).resolve().parent.parent / "models" / "lstm_model.pth"
        self.baseline_path = Path(__file__).resolve().parent.parent / "models" / "baseline_model.pkl"
        self.baseline_metadata_path = Path(__file__).resolve().parent.parent / "models" / "baseline_metadata.json"
        self.scaler_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "scaler.pkl"
        self.metadata_path = Path(__file__).resolve().parent.parent / "models" / "lstm_metadata.json"
        self.input_dim = 11
        self.scaler_width = self.input_dim + 1
        self.hidden_dim = 64
        self.model_kind = None
        self.model_label = "Unknown"
        self.feature_names = []
        self._loaded = False  # Lazy loading flag

    def _ensure_loaded(self):
        """Lazy load models only when needed"""
        if not self._loaded:
            self._load_model()
            self._loaded = True

    def _load_model(self):
        # Prefer the stronger linear baseline for production predictions.
        if self.baseline_path.exists():
            try:
                with open(self.baseline_path, "rb") as f:
                    self.model = pickle.load(f)
                if self.baseline_metadata_path.exists():
                    with open(self.baseline_metadata_path, "r", encoding="utf-8") as f:
                        baseline_metadata = json.load(f)
                    self.feature_names = baseline_metadata.get("feature_columns", []) or []
                    if self.feature_names:
                        self.input_dim = len(self.feature_names)
                self.model_kind = "linear"
                self.model_label = "Linear Regression"
                print("Baseline linear model loaded successfully.")
                return
            except Exception as e:
                print(f"Warning: Could not load baseline model: {e}")

        # Load Metadata
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                feature_columns = metadata.get("feature_columns", [])
                if feature_columns:
                    self.input_dim = len(feature_columns)
                    print(f"Metadata loaded. Input features: {self.input_dim}")
            except Exception as e:
                print(f"Warning: Could not load metadata: {e}")

        # Load Model
        if not self.model_path.exists():
            print(f"Warning: Model file not found at {self.model_path}")
        else:
            try:
                # Torch is optional in production because we prefer the baseline linear model.
                # Only import it if we actually need the LSTM fallback.
                import torch
                import torch.nn as nn

                class LSTMModel(nn.Module):
                    def __init__(self, input_dim, hidden_dim, output_dim=1, num_layers=2):
                        super().__init__()
                        self.hidden_dim = hidden_dim
                        self.num_layers = num_layers
                        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
                        self.fc = nn.Linear(hidden_dim, output_dim)

                    def forward(self, x):
                        x = x.unsqueeze(1)
                        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
                        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
                        out, _ = self.lstm(x, (h0, c0))
                        out = self.fc(out[:, -1, :])
                        return out

                self.model = LSTMModel(self.input_dim, self.hidden_dim)
                self.model.load_state_dict(torch.load(self.model_path, map_location="cpu"))
                self.model.eval()
                self.model_kind = "lstm"
                self.model_label = "LSTM"
                print("LSTM model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}")

        # Load Scaler
        if not self.scaler_path.exists():
            print(f"Warning: Scaler file not found at {self.scaler_path}")
        else:
            try:
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.scaler_width = int(getattr(self.scaler, "n_features_in_", self.input_dim + 1))
                print("Scaler loaded successfully.")
            except Exception as e:
                print(f"Error loading scaler: {e}")

    def predict(self, features, *, current_price: float | None = None):
        """
        Predicts crop price based on input features.
        Features should be a list or numpy array of length 11.
        Returns dict with prediction, confidence, and advice.
        """
        self._ensure_loaded()  # Lazy load only when prediction is needed
        
        if self.model is None:
            return None

        try:
            if len(features) != self.input_dim:
                raise ValueError(f"Expected {self.input_dim} features, got {len(features)}")

            if self.model_kind == "linear":
                input_array = np.asarray(features, dtype=np.float32).reshape(1, -1)
                if self.feature_names and len(self.feature_names) == input_array.shape[1]:
                    input_frame = pd.DataFrame(input_array, columns=self.feature_names)
                    pred = self.model.predict(input_frame)[0]
                else:
                    pred = self.model.predict(input_array)[0]
                
                confidence = self._calculate_confidence(features, pred, current_price=current_price)
                advice = self._generate_farmer_advice(
                    pred,
                    features,
                    confidence,
                    current_price=current_price,
                )
                
                return {
                    'prediction': float(pred),
                    'confidence': confidence,
                    'advice': advice,
                    'model_type': self.model_label
                }

            if self.scaler is None:
                return None

            # 1. Scale input features using the loaded scaler
            # The scaler was fitted on: ['Price', f1, f2, ... f11]
            dummy_in = np.zeros((1, self.scaler_width))
            dummy_in[0, 1:1 + self.input_dim] = features
            scaled_input = self.scaler.transform(dummy_in)
            scaled_features = scaled_input[0, 1:1 + self.input_dim]

            # 2. Make prediction
            input_tensor = torch.tensor(scaled_features, dtype=torch.float32).unsqueeze(0) # Add batch dimension
            with torch.no_grad():
                prediction = self.model(input_tensor)
            pred_scaled = prediction.item()

            # 3. Inverse scale the prediction
            dummy_out = np.zeros((1, self.scaler_width))
            dummy_out[0, 0] = pred_scaled
            unscaled_out = self.scaler.inverse_transform(dummy_out)
            pred_unscaled = unscaled_out[0, 0]

            # Calculate confidence and advice
            confidence = self._calculate_confidence(features, pred_unscaled, current_price=current_price)
            advice = self._generate_farmer_advice(
                pred_unscaled,
                features,
                confidence,
                current_price=current_price,
            )

            return {
                'prediction': pred_unscaled,
                'confidence': confidence,
                'advice': advice,
                'model_type': self.model_label
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            return None

    def _calculate_confidence(self, features, prediction, *, current_price: float | None = None):
        """Heuristic confidence score (0.5..0.95) based on signal quality and price stability.

        NOTE: In this app the feature vector is ordered like:
        [temperature, precipitation, humidity, sentiment, price_lag_1..price_lag_7]
        so we must not treat features[0] as the current price.
        """
        try:
            base_confidence = 0.85 if self.model_kind == "linear" else 0.75

            temp = float(features[0]) if len(features) > 0 else 25.0
            precip = float(features[1]) if len(features) > 1 else 0.0
            sentiment = float(features[3]) if len(features) > 3 else 0.0

            lag_prices = []
            if len(features) > 4:
                lag_prices = [float(v) for v in features[4:] if v is not None]

            # Price stability: higher volatility => lower confidence.
            volatility_conf = 0.75
            if lag_prices:
                series = np.asarray(lag_prices, dtype=np.float32)
                mean = float(np.mean(series))
                std = float(np.std(series))
                vol = (std / (mean + 1e-6)) if mean > 0 else 0.5
                # Map volatility (0..0.35+) -> confidence (0.90..0.55)
                volatility_conf = float(np.clip(0.90 - (vol / 0.35) * 0.35, 0.55, 0.92))

            # Signal strength: strong sentiment slightly increases confidence; neutral slightly reduces.
            sent_abs = abs(sentiment)
            sentiment_conf = float(np.clip(0.70 + min(sent_abs, 1.0) * 0.18, 0.65, 0.90))

            # Weather extremes tend to make short-term forecasts harder.
            weather_penalty = 0.0
            if precip > 200:
                weather_penalty += 0.06
            if precip < 10:
                weather_penalty += 0.04
            if temp >= 34:
                weather_penalty += 0.04
            if temp <= 15:
                weather_penalty += 0.03

            # Big predicted swings are riskier unless supported by stable history.
            delta_penalty = 0.0
            if current_price and current_price > 0:
                delta = abs(float(prediction) - float(current_price)) / float(current_price)
                delta_penalty = float(np.clip((delta / 0.30) * 0.08, 0.0, 0.08))

            final_confidence = (
                base_confidence * 0.55
                + volatility_conf * 0.25
                + sentiment_conf * 0.20
                - weather_penalty
                - delta_penalty
            )
            return round(min(max(final_confidence, 0.5), 0.95), 2)  # Clamp between 0.5 and 0.95
            
        except Exception as e:
            print(f"Confidence calculation error: {e}")
            return 0.75  # Default confidence

    def _generate_farmer_advice(self, predicted_price, features, confidence, *, current_price: float | None = None):
        """Generate farmer advice based on expected price movement.

        This app's UI is phrased for farmers deciding when to sell existing stock.
        If the model expects prices to rise, the user should generally HOLD and sell later.
        If the model expects prices to fall, the user should SELL sooner.
        """
        try:
            temp = float(features[0]) if len(features) > 0 else 25.0
            precipitation = float(features[1]) if len(features) > 1 else 0.0
            sentiment = float(features[3]) if len(features) > 3 else 0.0
            current = float(current_price) if current_price is not None else 0.0

            # Calculate price change
            predicted = float(predicted_price) if predicted_price is not None else current
            price_change_percent = ((predicted - current) / current * 100) if current > 0 else 0.0
            
            # Generate advice based on price prediction and conditions
            advice = {
                'action': 'HOLD',
                'reasoning': '',
                'timeframe': '2-4 weeks',
                'risk_level': 'MEDIUM',
                'weather_impact': '',
                'market_sentiment': ''
            }
            
            # Price change analysis (sell-stock framing)
            if price_change_percent <= -10:
                advice['action'] = 'SELL_NOW'
                advice['reasoning'] = f'Prices expected to drop by {abs(price_change_percent):.1f}% — sell now to avoid losses'
                advice['risk_level'] = 'LOW' if confidence >= 0.8 else 'MEDIUM'
                advice['timeframe'] = 'Immediate'
            elif price_change_percent <= -5:
                advice['action'] = 'SELL_SOON'
                advice['reasoning'] = f'Small price drop expected ({abs(price_change_percent):.1f}%) — consider selling within 1–2 weeks'
                advice['timeframe'] = '1-2 weeks'
            elif price_change_percent >= 10:
                advice['action'] = 'HOLD'
                advice['reasoning'] = f'Prices expected to rise by {price_change_percent:.1f}% — hold and sell later for a better price'
                advice['risk_level'] = 'MEDIUM'
                advice['timeframe'] = '2-4 weeks'
            elif price_change_percent >= 5:
                advice['action'] = 'HOLD'
                advice['reasoning'] = f'Moderate price increase expected ({price_change_percent:.1f}%) — hold for 1–2 weeks if you can store safely'
                advice['timeframe'] = '1-2 weeks'
            else:
                advice['action'] = 'HOLD'
                advice['reasoning'] = 'Prices expected to stay fairly stable — no urgent action needed; monitor weekly'
                advice['timeframe'] = '1-2 weeks'
            
            # Weather impact analysis
            if precipitation > 150:
                advice['weather_impact'] = 'Heavy rains may improve crop yields and potentially lower prices'
                if advice['action'] == 'HOLD' and price_change_percent > 0:
                    advice['reasoning'] += ' (Watch for harvest-driven supply increases.)'
            elif precipitation < 50:
                advice['weather_impact'] = 'Low rainfall may reduce supply and increase prices'
                if advice['action'] == 'HOLD' and price_change_percent >= 0:
                    advice['reasoning'] += ' (Dry conditions may support higher prices.)'
            else:
                advice['weather_impact'] = 'Normal weather conditions expected'
            
            # Market sentiment analysis
            if sentiment > 0.3:
                advice['market_sentiment'] = 'Positive market sentiment supports price increases'
            elif sentiment < -0.3:
                advice['market_sentiment'] = 'Negative market sentiment may pressure prices downward'
            else:
                advice['market_sentiment'] = 'Neutral market sentiment - prices driven by fundamentals'
            
            # Adjust for confidence
            if confidence < 0.7:
                advice['risk_level'] = 'HIGH'
                advice['reasoning'] += f' (Note: Low prediction confidence: {confidence*100:.0f}%)'
            elif confidence > 0.9:
                advice['risk_level'] = 'LOW'
                advice['reasoning'] += f' (High confidence: {confidence*100:.0f}%)'
            
            return advice
            
        except Exception as e:
            print(f"Advice generation error: {e}")
            return {
                'action': 'HOLD',
                'reasoning': 'Unable to generate specific advice - monitor market conditions',
                'timeframe': '2-4 weeks',
                'risk_level': 'MEDIUM',
                'weather_impact': 'Weather conditions being monitored',
                'market_sentiment': 'Market sentiment analysis unavailable'
            }

# Singleton instance
prediction_service = PredictionService()
