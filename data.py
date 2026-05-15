from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from app.prediction import prediction_service
from app.refresh_state import build_refresh_label, get_refresh_state
from app.translations import get_sentence
from app.cache import cache_result
from app.number_words import localized_number_words

from . import database, models


CROP_METADATA: Dict[str, Dict[str, str]] = {
    "matooke": {
        "name": "Matooke",
        "unit": "UGX/bunch",
        "image": "/static/images/matooke.png",
    },
    "cassava": {
        "name": "Cassava",
        "unit": "UGX/kg",
        "image": "/static/images/cassava.png",
    },
    "coffee": {
        "name": "Coffee",
        "unit": "UGX/kg",
        "image": "/static/images/coffee.png",
    },
    "maize": {
        "name": "Maize",
        "unit": "UGX/kg",
        "image": "/static/images/maize.png",
    },
    "beans": {
        "name": "Beans",
        "unit": "UGX/kg",
        "image": "/static/images/beans.png",
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


def _normalize_key(value) -> str:
    return str(value).strip().lower()


def _normalize_crop_id(crop_id: str) -> str:
    return _normalize_key(crop_id)


def _normalize_region(region: str) -> str:
    key = _normalize_key(region)
    return REGION_ALIASES.get(key, key)


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


def _market_db_name(region_slug: str) -> str:
    normalized = _normalize_region(region_slug)
    return REGION_DB_MARKETS.get(normalized, normalized.replace("_", " ").title())


def _market_display_name(region_slug: str) -> str:
    normalized = _normalize_region(region_slug)
    return REGION_DISPLAY_NAMES.get(normalized, f"{normalized.replace('_', ' ').title()} Market")


def _fallback_price(crop_id: str) -> float:
    normalized = _normalize_crop_id(crop_id)
    return float(FALLBACK_CURRENT_PRICES.get(normalized, 1000.0))


def _is_valid_number(value) -> bool:
    try:
        number = float(value)
        return number == number
    except Exception:
        return False


def _query_price_records(db, crop_id: str, region_slug: str):
    crop_name = _crop_meta(crop_id)["name"]
    market_name = _market_db_name(region_slug)

    exact_rows = (
        db.query(models.PriceObservation)
        .filter(
            models.PriceObservation.crop == crop_name,
            models.PriceObservation.market == market_name,
        )
        .order_by(models.PriceObservation.date.asc(), models.PriceObservation.id.asc())
        .all()
    )
    if exact_rows:
        return exact_rows, "regional price history", market_name

    crop_rows = (
        db.query(models.PriceObservation)
        .filter(models.PriceObservation.crop == crop_name)
        .order_by(models.PriceObservation.date.asc(), models.PriceObservation.id.asc())
        .all()
    )
    if crop_rows:
        return crop_rows, "crop-level fallback history", market_name

    return [], "fallback price series", market_name


def _query_regional_signal(db, crop_id: str, region_slug: str):
    crop_key = _normalize_crop_id(crop_id)
    region_key = _normalize_region(region_slug)

    signal = (
        db.query(models.RegionalSignal)
        .filter(
            models.RegionalSignal.crop == crop_key,
            models.RegionalSignal.region == region_key,
        )
        .order_by(models.RegionalSignal.date.desc(), models.RegionalSignal.id.desc())
        .first()
    )
    if signal:
        return signal, "regional signal", signal.date

    market_feature = (
        db.query(models.MarketFeature)
        .order_by(models.MarketFeature.date.desc())
        .first()
    )
    if market_feature:
        return market_feature, "global market snapshot", market_feature.date

    return None, "default market signal", None


def _query_data_refresh_label(db):
    refresh_state = get_refresh_state(db)
    if refresh_state and refresh_state.status in {"success", "partial"}:
        label = build_refresh_label(refresh_state.refreshed_at)
        if label:
            return label, refresh_state.refreshed_at
    return None, None


def _build_lag_features(price_values: List[float], fallback_price: float):
    series = [float(value) for value in price_values if _is_valid_number(value)]
    if not series:
        series = [float(fallback_price)]

    current_price = float(series[-1])
    prior_prices = series[:-1]
    if not prior_prices:
        prior_prices = [current_price]

    if len(prior_prices) < 7:
        prior_prices = [prior_prices[0]] * (7 - len(prior_prices)) + prior_prices

    lag_values = list(reversed(prior_prices[-7:]))
    return current_price, lag_values


def _fallback_history(current_price: float, days: int = 8):
    today = datetime.now().date()
    return [
        {
            "date": (today - timedelta(days=(days - idx - 1))).strftime("%Y-%m-%d"),
            "price": int(round(current_price)),
        }
        for idx in range(days)
    ]


@cache_result(ttl_seconds=300)
def _build_detail_context(crop_id: str, region: str):
    crop_id = _normalize_crop_id(crop_id)
    region_slug = _normalize_region(region)
    meta = _crop_meta(crop_id)
    fallback_price = _fallback_price(crop_id)

    db = database.SessionLocal()
    try:
        price_rows, series_scope, market_name = _query_price_records(db, crop_id, region_slug)
        history = []
        price_values: List[float] = []

        for row in price_rows[-30:]:
            if not _is_valid_number(row.price):
                continue
            price_value = float(row.price)
            price_values.append(price_value)
            history.append({"date": row.date, "price": int(round(price_value))})

        if not price_values:
            price_values = [fallback_price]
            history = _fallback_history(fallback_price)

        current_price, lag_features = _build_lag_features(price_values, fallback_price)
        signal_row, signal_scope, signal_date = _query_regional_signal(db, crop_id, region_slug)
        refresh_label, refresh_timestamp = _query_data_refresh_label(db)

        if signal_row is not None:
            temp = float(getattr(signal_row, "temperature", 25.0) or 25.0)
            precip = float(getattr(signal_row, "precipitation", 0.0) or 0.0)
            humidity = float(getattr(signal_row, "humidity", 70.0) or 70.0)
            sentiment = float(getattr(signal_row, "sentiment_score", 0.0) or 0.0)
        else:
            temp, precip, humidity, sentiment = 25.0, 0.0, 70.0, 0.0

        features = [temp, precip, humidity, sentiment] + lag_features
        prediction_result = prediction_service.predict(features, current_price=current_price)
        
        # Handle new prediction format
        if prediction_result is None:
            predicted_val = current_price
            confidence = 0.75
            advice = {
                'action': 'HOLD',
                'reasoning': 'Unable to generate specific advice - monitor market conditions',
                'timeframe': '2-4 weeks',
                'risk_level': 'MEDIUM',
                'weather_impact': 'Weather conditions being monitored',
                'market_sentiment': 'Market sentiment analysis unavailable'
            }
        elif isinstance(prediction_result, dict):
            predicted_val = prediction_result.get('prediction', current_price)
            confidence = prediction_result.get('confidence', 0.75)
            advice = prediction_result.get('advice', {
                'action': 'HOLD',
                'reasoning': 'Unable to generate specific advice - monitor market conditions',
                'timeframe': '2-4 weeks',
                'risk_level': 'MEDIUM',
                'weather_impact': 'Weather conditions being monitored',
                'market_sentiment': 'Market sentiment analysis unavailable'
            })
        else:
            # Legacy format - single prediction value
            predicted_val = prediction_result
            confidence = 0.75
            advice = {
                'action': 'HOLD',
                'reasoning': 'Unable to generate specific advice - monitor market conditions',
                'timeframe': '2-4 weeks',
                'risk_level': 'MEDIUM',
                'weather_impact': 'Weather conditions being monitored',
                'market_sentiment': 'Market sentiment analysis unavailable'
            }
        
        if not _is_valid_number(predicted_val):
            predicted_val = current_price

        predicted_price = max(0.0, float(predicted_val))
        predicted_price_int = int(round(predicted_price))
        current_price_int = int(round(current_price))

        model_label = getattr(prediction_service, "model_label", "AI Model")
        prediction_source = (
            f"AI Model ({model_label}) - {signal_scope}; {series_scope}; {len(history)} price points"
        )

        if signal_date:
            last_updated_label = (
                f"Prices through {history[-1]['date']}; signals through {signal_date}"
            )
        else:
            last_updated_label = f"Prices through {history[-1]['date']}; no regional signal yet"

        data_freshness_label = refresh_label or last_updated_label
        data_freshness_timestamp = refresh_timestamp or signal_date or history[-1]["date"]

        delta = predicted_price - current_price
        price_change_percent = ((predicted_price - current_price) / current_price * 100) if current_price > 0 else 0
        
        # Use the enhanced advice from prediction service
        enhanced_advice = advice.get('action', 'HOLD')
        enhanced_reasoning = advice.get('reasoning', 'Monitor market conditions')
        risk_level = advice.get('risk_level', 'MEDIUM')
        timeframe = advice.get('timeframe', '2-4 weeks')
        weather_impact = advice.get('weather_impact', 'Weather conditions being monitored')
        market_sentiment = advice.get('market_sentiment', 'Market sentiment analysis unavailable')

        # Build comprehensive advice description
        if price_change_percent >= 5:
            advice_desc = enhanced_reasoning
        elif price_change_percent <= -5:
            advice_desc = enhanced_reasoning
        else:
            advice_desc = enhanced_reasoning

        # Weather analysis
        if precip > 150:
            weather = "Heavy Rain Expected"
        elif precip < 50:
            weather = "Dry Conditions Expected"
        elif temp >= 30:
            weather = "Hot Conditions"
        elif sentiment > 0.1:
            weather = "Positive Market Signal"
        elif sentiment < -0.1:
            weather = "Weak Market Signal"
        else:
            weather = "Favorable Conditions"

        weather_desc = (
            f"Latest signal for {market_name} on {signal_date or history[-1]['date']}: "
            f"{temp:.1f} C, {humidity:.0f}% humidity, {precip:.1f} mm rainfall, "
            f"sentiment {sentiment:+.2f}. {weather_impact}"
        )

        return {
            "id": crop_id,
            "name": meta["name"],
            "region": region_slug,
            "market": market_name,
            "current_price": f"{current_price_int:,}",
            "current_price_raw": current_price,
            "predicted_price": f"{predicted_price_int:,}",
            "predicted_price_raw": predicted_price,
            "prediction_source": prediction_source,
            "unit": meta["unit"],
            "history": history,
            "feature_names": FEATURE_NAMES,
            "feature_vector": features,
            "feature_map": dict(zip(FEATURE_NAMES, features)),
            "voice_texts": {
                lang: get_sentence(
                    crop_id,
                    market_name,
                    localized_number_words(str(current_price_int), lang),
                    localized_number_words(str(predicted_price_int), lang),
                    lang,
                )
                for lang in ("en", "lg", "rn", "teo", "luo", "sw")
            },
            "advice": enhanced_advice,
            "advice_desc": advice_desc,
            "confidence": confidence,
            "risk_level": risk_level,
            "timeframe": timeframe,
            "weather": weather,
            "weather_desc": weather_desc,
            "weather_impact": weather_impact,
            "market_sentiment": market_sentiment,
            "temperature": temp,
            "precipitation": precip,
            "humidity": humidity,
            "sentiment_score": sentiment,
            "last_updated_label": last_updated_label,
            "data_freshness_label": data_freshness_label,
            "data_freshness_timestamp": data_freshness_timestamp,
        }
    finally:
        db.close()


def _build_crop_card(crop_id: str, region: str):
    detail = _build_detail_context(crop_id, region)
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


@cache_result(ttl_seconds=300)  # Cache for 5 minutes
def get_monitored_crops():
    return [_build_crop_card(crop_id, region) for crop_id, region in DEFAULT_MONITORED_PAIRS]


@cache_result(ttl_seconds=300)
def get_custom_monitored_crops(crop_pairs):
    """Returns metadata for a custom list of (crop_id, region) pairs."""
    if not crop_pairs:
        return []
    return [_build_crop_card(crop_id, region) for crop_id, region in crop_pairs]


@cache_result(ttl_seconds=600)  # Cache for 10 minutes
def get_crop_detail(crop_id, region):
    """Returns detailed data for a specific crop."""
    return _build_detail_context(crop_id, region)
