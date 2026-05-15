"""
Optimized data access layer with bulk operations and caching
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from functools import lru_cache
import pandas as pd

from app.prediction import prediction_service
from app.refresh_state import build_refresh_label, get_refresh_state
from app.translations import get_sentence
from app.cache import cache_result
from app import database, models

# Static data - cache at module level for instant access
CROP_METADATA: Dict[str, Dict[str, str]] = {
    "matooke": {
        "name": "Matooke",
        "unit": "UGX/bunch",
        "image": "https://images.unsplash.com/photo-1603052875302-d376b7c0638a?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60",
    },
    "cassava": {
        "name": "Cassava",
        "unit": "UGX/kg",
        "image": "https://images.unsplash.com/photo-1596097635121-14b63b7a0c19?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60",
    },
    "coffee": {
        "name": "Coffee",
        "unit": "UGX/kg",
        "image": "https://images.unsplash.com/photo-1552346988-186312d44647?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60",
    },
    "maize": {
        "name": "Maize",
        "unit": "UGX/kg",
        "image": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60",
    },
    "beans": {
        "name": "Beans",
        "unit": "UGX/kg",
        "image": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=60",
    },
}

DEFAULT_MONITORED_PAIRS: List[Tuple[str, str]] = [
    ("matooke", "nakawa"),
    ("cassava", "gulu"),
    ("coffee", "mbale"),
    ("maize", "kasese"),
    ("beans", "owino"),
]

REGION_ALIASES = {
    "nakawa": "nakawa",
    "nakawa market": "nakawa",
    "kampala": "nakawa",
    "owino": "owino",
    "owino market": "owino",
    "kalerwe": "kalerwe",
    "kalerwe market": "kalerwe",
    "masaka": "masaka",
    "masaka market": "masaka",
    "mbale": "mbale",
    "mbale market": "mbale",
    "gulu": "gulu",
    "gulu market": "gulu",
    "kasese": "kasese",
    "kasese market": "kasese",
}

REGION_DB_MARKETS = {
    "nakawa": "Nakawa",
    "owino": "Owino",
    "kalerwe": "Kalerwe",
    "masaka": "Masaka",
    "mbale": "Mbale",
    "gulu": "Gulu",
    "kasese": "Kasese",
}

REGION_DISPLAY_NAMES = {
    "nakawa": "Nakawa Market",
    "owino": "Owino Market",
    "kalerwe": "Kalerwe Market",
    "masaka": "Masaka Market",
    "mbale": "Mbale Market",
    "gulu": "Gulu Market",
    "kasese": "Kasese Market",
}

FALLBACK_CURRENT_PRICES = {
    "matooke": 15000.0,
    "cassava": 2500.0,
    "coffee": 8000.0,
    "maize": 1200.0,
    "beans": 3500.0,
}

FEATURE_NAMES = [
    "temperature_2m",
    "precipitation",
    "humidity_2m",
    "sentiment_score",
    "price_lag_1",
    "price_lag_2",
    "price_lag_3",
    "price_lag_4",
    "price_lag_5",
    "price_lag_6",
    "price_lag_7",
]

# Fast lookup functions with LRU cache
@lru_cache(maxsize=128)
def _normalize_key(value) -> str:
    return str(value).strip().lower()

@lru_cache(maxsize=128)
def _normalize_crop_id(crop_id: str) -> str:
    return _normalize_key(crop_id)

@lru_cache(maxsize=128)
def _normalize_region(region: str) -> str:
    key = _normalize_key(region)
    return REGION_ALIASES.get(key, key)

@lru_cache(maxsize=128)
def _crop_meta(crop_id: str) -> Dict[str, str]:
    normalized = _normalize_crop_id(crop_id)
    return CROP_METADATA.get(
        normalized,
        {
            "name": normalized.replace("_", " ").title() if normalized else "Crop",
            "unit": "UGX/kg",
            "image": CROP_METADATA["maize"]["image"],
        },
    )

@lru_cache(maxsize=128)
def _market_db_name(region_slug: str) -> str:
    normalized = _normalize_region(region_slug)
    return REGION_DB_MARKETS.get(normalized, normalized.replace("_", " ").title())

@lru_cache(maxsize=128)
def _market_display_name(region_slug: str) -> str:
    normalized = _normalize_region(region_slug)
    return REGION_DISPLAY_NAMES.get(normalized, f"{normalized.replace('_', ' ').title()} Market")

@lru_cache(maxsize=128)
def _fallback_price(crop_id: str) -> float:
    normalized = _normalize_crop_id(crop_id)
    return float(FALLBACK_CURRENT_PRICES.get(normalized, 1000.0))

def _is_valid_number(value) -> bool:
    try:
        number = float(value)
        return number == number
    except Exception:
        return False

# Bulk data loading for better performance
@cache_result(ttl_seconds=300)
def _load_all_price_data():
    """Load all price data in one query"""
    db = database.SessionLocal()
    try:
        all_prices = db.query(models.PriceObservation).all()
        # Convert to DataFrame for faster processing
        df = pd.DataFrame([{
            'date': p.date,
            'crop': p.crop,
            'market': p.market,
            'price': p.price,
            'unit': p.unit
        } for p in all_prices])
        return df
    finally:
        db.close()

@cache_result(ttl_seconds=600)
def _load_all_regional_signals():
    """Load all regional signals in one query"""
    db = database.SessionLocal()
    try:
        all_signals = db.query(models.RegionalSignal).all()
        return {
            f"{s.crop}_{s.region}": s
            for s in all_signals
        }
    finally:
        db.close()

def _build_detail_context_fast(crop_id: str, region: str):
    """Optimized detail context building"""
    crop_id = _normalize_crop_id(crop_id)
    region_slug = _normalize_region(region)
    meta = _crop_meta(crop_id)
    fallback_price = _fallback_price(crop_id)
    
    # Use bulk loaded data
    price_df = _load_all_price_data()
    signals = _load_all_regional_signals()
    
    # Filter data for this crop/region
    crop_name = meta["name"]
    market_name = _market_db_name(region_slug)
    
    # Price data
    crop_prices = price_df[(price_df['crop'] == crop_name)]
    if not crop_prices.empty:
        region_prices = crop_prices[crop_prices['market'] == market_name]
        if not region_prices.empty:
            price_data = region_prices.sort_values('date')
        else:
            price_data = crop_prices.sort_values('date')
    else:
        # Fallback data
        today = datetime.now().date()
        price_data = pd.DataFrame([
            {'date': (today - timedelta(days=i)).strftime("%Y-%m-%d"), 'price': fallback_price}
            for i in range(7, 0, -1)
        ])
    
    # Get current price and history
    if not price_data.empty:
        current_price = float(price_data.iloc[-1]['price'])
        history = [
            {"date": row['date'], "price": int(round(row['price']))}
            for _, row in price_data.tail(30).iterrows()
        ]
    else:
        current_price = fallback_price
        history = []
    
    # Build lag features
    if not price_data.empty:
        price_values = [float(p) for p in price_data['price'].tail(8).tolist()]
    else:
        price_values = [fallback_price]
    
    if len(price_values) < 8:
        price_values = [price_values[0]] * (8 - len(price_values)) + price_values
    
    lag_features = list(reversed(price_values[-7:]))
    
    # Get regional signal
    signal_key = f"{crop_id}_{region_slug}"
    signal = signals.get(signal_key)
    
    if signal:
        temp = float(signal.temperature or 25.0)
        precip = float(signal.precipitation or 0.0)
        humidity = float(signal.humidity or 70.0)
        sentiment = float(signal.sentiment_score or 0.0)
        signal_date = signal.date
    else:
        temp, precip, humidity, sentiment = 25.0, 0.0, 70.0, 0.0
        signal_date = None
    
    # Prediction
    features = [temp, precip, humidity, sentiment] + lag_features
    predicted_val = prediction_service.predict(features)
    if predicted_val is None:
        predicted_val = current_price
    
    predicted_price = max(0.0, float(predicted_val))
    current_price_int = int(round(current_price))
    predicted_price_int = int(round(predicted_price))
    
    # Advice logic
    delta = predicted_price - current_price
    if delta >= 0:
        advice = "WAIT TO SELL"
        advice_desc = f"The model expects a rise from {current_price_int:,} UGX to {predicted_price_int:,} UGX."
    else:
        advice = "SELL NOW"
        advice_desc = f"The model expects a dip from {current_price_int:,} UGX to {predicted_price_int:,} UGX."
    
    # Weather conditions
    if precip > 15:
        weather = "Wet Conditions"
    elif temp >= 30:
        weather = "Hot Conditions"
    elif sentiment > 0.1:
        weather = "Positive Market Signal"
    elif sentiment < -0.1:
        weather = "Weak Market Signal"
    else:
        weather = "Favorable Conditions"
    
    return {
        "id": crop_id,
        "name": meta["name"],
        "region": region_slug,
        "market": market_name,
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
            lang: get_sentence(crop_id, market_name, str(current_price_int), str(predicted_price_int), lang)
            for lang in ("en", "lg", "rn", "teo", "luo", "sw")
        },
        "advice": advice,
        "advice_desc": advice_desc,
        "weather": weather,
        "temperature": temp,
        "precipitation": precip,
        "humidity": humidity,
        "sentiment_score": sentiment,
        "last_updated_label": f"Prices through {history[-1]['date'] if history else 'Unknown'}",
        "data_freshness_label": f"Prices through {history[-1]['date'] if history else 'Unknown'}",
        "data_freshness_timestamp": signal_date or (history[-1]['date'] if history else datetime.now().strftime("%Y-%m-%d")),
    }

def _build_crop_card_fast(crop_id: str, region: str):
    """Optimized crop card building"""
    detail = _build_detail_context_fast(crop_id, region)
    meta = _crop_meta(crop_id)
    return {
        "name": detail["name"],
        "market": _market_display_name(region),
        "price": detail["current_price"],
        "unit": meta["unit"],
        "image": meta["image"],
        "id": detail["id"],
        "region": detail["region"],
        "freshness_label": detail["data_freshness_label"],
    }

@cache_result(ttl_seconds=300)
def get_monitored_crops_fast():
    """Fast monitored crops with bulk loading"""
    return [_build_crop_card_fast(crop_id, region) for crop_id, region in DEFAULT_MONITORED_PAIRS]

@cache_result(ttl_seconds=300)
def get_custom_monitored_crops_fast(crop_pairs):
    """Fast custom monitored crops"""
    if not crop_pairs:
        return []
    return [_build_crop_card_fast(crop_id, region) for crop_id, region in crop_pairs]

@cache_result(ttl_seconds=600)
def get_crop_detail_fast(crop_id, region):
    """Fast crop detail with optimized loading"""
    return _build_detail_context_fast(crop_id, region)
