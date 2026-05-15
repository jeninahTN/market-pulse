"""
Lightweight performance optimizations for data layer
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from functools import lru_cache
import time
import os

from app.prediction import prediction_service
from app.refresh_state import build_refresh_label, get_refresh_state
from app.translations import get_sentence
from app.number_words import localized_number_words
from app.cache import cache_result
from app import database, models
from app.data import (
    CROP_METADATA, DEFAULT_MONITORED_PAIRS, REGION_ALIASES, REGION_DB_MARKETS,
    REGION_DISPLAY_NAMES, FALLBACK_CURRENT_PRICES, FEATURE_NAMES,
    _normalize_key, _normalize_crop_id, _normalize_region, _crop_meta,
    _market_db_name, _market_display_name, _fallback_price, _is_valid_number
)

# Enhanced caching with longer TTL for static data
@cache_result(ttl_seconds=1800)  # 30 minutes
def get_monitored_crops_ultra_fast():
    """Ultra-fast monitored crops with aggressive caching"""
    return [_build_crop_card_optimized(crop_id, region) for crop_id, region in DEFAULT_MONITORED_PAIRS]

@cache_result(ttl_seconds=1800)
def get_custom_monitored_crops_ultra_fast(crop_pairs):
    """Ultra-fast custom monitored crops"""
    if not crop_pairs:
        return []
    return [_build_crop_card_optimized(crop_id, region) for crop_id, region in crop_pairs]

# Detail views should feel "real time" when users request a new prediction.
# Keep TTL short and configurable so deployments can tune load vs freshness.
_DETAIL_CACHE_TTL_SECONDS = int(os.getenv("MARKET_PULSE_DETAIL_CACHE_TTL_SECONDS", "120"))
@cache_result(ttl_seconds=_DETAIL_CACHE_TTL_SECONDS)
def get_crop_detail_ultra_fast(crop_id, region):
    """Ultra-fast crop detail with extended caching"""
    return _build_detail_context_optimized(crop_id, region)

def _build_crop_card_optimized(crop_id: str, region: str):
    """Optimized crop card without full detail loading"""
    crop_id = _normalize_crop_id(crop_id)
    region_slug = _normalize_region(region)
    meta = _crop_meta(crop_id)
    
    # Use fallback price for card display (no DB query)
    fallback_price = _fallback_price(crop_id)
    current_price_int = int(round(fallback_price))
    
    return {
        "name": meta["name"],
        "market": _market_display_name(region),
        "price": f"{current_price_int:,}",
        "unit": meta["unit"],
        "image": meta["image"],
        "id": crop_id,
        "region": region_slug,
        "freshness_label": "Cached data",
    }

def _build_detail_context_optimized(crop_id: str, region: str):
    """Optimized detail context with minimal DB queries"""
    crop_id = _normalize_crop_id(crop_id)
    region_slug = _normalize_region(region)
    meta = _crop_meta(crop_id)
    fallback_price = _fallback_price(crop_id)

    # Single database session for all queries
    db = database.SessionLocal()
    try:
        # Optimized price query with limit
        price_rows = (
            db.query(models.PriceObservation)
            .filter(
                models.PriceObservation.crop == meta["name"],
                models.PriceObservation.market == _market_db_name(region_slug)
            )
            .order_by(models.PriceObservation.date.desc())
            .limit(30)  # Only get last 30 records
            .all()
        )
        
        # Optimized signal query
        signal = (
            db.query(models.RegionalSignal)
            .filter(
                models.RegionalSignal.crop == crop_id,
                models.RegionalSignal.region == region_slug
            )
            .order_by(models.RegionalSignal.date.desc())
            .first()
        )
        
        # Quick history from limited data
        history = []
        price_values = []
        
        if price_rows:
            for row in reversed(price_rows[-15:]):  # Only last 15 for speed
                if _is_valid_number(row.price):
                    price_val = float(row.price)
                    price_values.append(price_val)
                    history.append({
                        "date": row.date, 
                        "price": int(round(price_val))
                    })
        
        # Use fallback if no data
        if not price_values:
            price_values = [fallback_price]
            current_price = fallback_price
            history = [
                {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "price": int(round(fallback_price))}
                for i in range(7, 0, -1)
            ]
        else:
            current_price = price_values[-1]
        
        # Build minimal lag features
        if len(price_values) < 7:
            price_values = [price_values[0]] * (7 - len(price_values)) + price_values
        
        lag_features = list(reversed(price_values[-7:]))
        
        # Signal data with defaults
        if signal:
            temp = float(signal.temperature or 25.0)
            precip = float(signal.precipitation or 0.0)
            humidity = float(signal.humidity or 70.0)
            sentiment = float(signal.sentiment_score or 0.0)
            signal_date = signal.date
        else:
            temp, precip, humidity, sentiment = 25.0, 0.0, 70.0, 0.0
            signal_date = None
        
        # Fast prediction
        features = [temp, precip, humidity, sentiment] + lag_features
        prediction_result = prediction_service.predict(features, current_price=current_price)
        
        # Handle new prediction format
        if prediction_result is None:
            predicted_val = current_price
            confidence = 0.75
            advice_action = 'HOLD'
            advice_desc = 'Monitor market conditions'
            risk_level = 'MEDIUM'
            timeframe = '2-4 weeks'
        elif isinstance(prediction_result, dict):
            predicted_val = prediction_result.get('prediction', current_price)
            confidence = prediction_result.get('confidence', 0.75)
            advice_data = prediction_result.get('advice', {})
            advice_action = advice_data.get('action', 'HOLD')
            advice_desc = advice_data.get('reasoning', 'Monitor market conditions')
            risk_level = advice_data.get('risk_level', 'MEDIUM')
            timeframe = advice_data.get('timeframe', '2-4 weeks')
        else:
            # Legacy format
            predicted_val = prediction_result
            confidence = 0.75
            advice_action = 'HOLD'
            advice_desc = 'Monitor market conditions'
            risk_level = 'MEDIUM'
            timeframe = '2-4 weeks'
        
        if predicted_val is None:
            predicted_val = current_price
        
        predicted_price = max(0.0, float(predicted_val))
        current_price_int = int(round(current_price))
        predicted_price_int = int(round(predicted_price))
        
        return {
            "id": crop_id,
            "name": meta["name"],
            "region": region_slug,
            "market": _market_db_name(region_slug),
            "current_price": f"{current_price_int:,}",
            "current_price_raw": current_price,
            "predicted_price": f"{predicted_price_int:,}",
            "predicted_price_raw": predicted_price,
            "prediction_source": f"AI Model ({getattr(prediction_service, 'model_label', 'AI Model')})",
            "unit": meta["unit"],
            "history": history,
            "feature_names": FEATURE_NAMES,
            "feature_vector": features,
            "feature_map": dict(zip(FEATURE_NAMES, features)),
            "voice_texts": {
                lang: get_sentence(
                    crop_id,
                    _market_db_name(region_slug),
                    localized_number_words(str(current_price_int), lang),
                    localized_number_words(str(predicted_price_int), lang),
                    lang,
                )
                for lang in ("en", "lg", "rn", "teo", "luo", "sw")
            },
            "advice": advice_action,
            "advice_desc": advice_desc,
            "confidence": confidence,
            "risk_level": risk_level,
            "timeframe": timeframe,
            "weather": "Favorable Conditions",
            "temperature": temp,
            "precipitation": precip,
            "humidity": humidity,
            "sentiment_score": sentiment,
            "weather_impact": _get_weather_impact(precip, temp),
            "market_sentiment": _get_market_sentiment(sentiment),
            "last_updated_label": f"Prices through {history[-1]['date'] if history else 'Unknown'}",
            "data_freshness_label": f"Prices through {history[-1]['date'] if history else 'Unknown'}",
            "data_freshness_timestamp": signal_date or (history[-1]['date'] if history else datetime.now().strftime("%Y-%m-%d")),
        }
    finally:
        db.close()


def _get_weather_impact(precipitation: float, temperature: float) -> str:
    """Generate weather impact description based on conditions"""
    if precipitation > 150:
        return "Heavy rains may improve crop yields and potentially lower prices"
    elif precipitation < 50:
        return "Low rainfall may reduce supply and increase prices"
    else:
        return "Normal weather conditions expected"


def _get_market_sentiment(sentiment_score: float) -> str:
    """Generate market sentiment description based on sentiment score"""
    if sentiment_score > 0.3:
        return "Positive market sentiment supports price increases"
    elif sentiment_score < -0.3:
        return "Negative market sentiment may pressure prices downward"
    else:
        return "Neutral market sentiment - prices driven by fundamentals"
