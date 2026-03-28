import datetime

from flask import Blueprint, current_app, jsonify, request, session

from app.repositories.market_intelligence_repository import MarketIntelligenceRepository
from app.extensions import csrf
from app.services.exceptions import ServiceError
from app.services.market_intelligence_service import MarketIntelligenceService
from app.services.weather_suggestion_service import generate_weather_crop_suggestions
from app.services.weather_client import WeatherClient
from app.utils.request_auth import extract_user_identity


farmer_bp = Blueprint("farmer", __name__, url_prefix="/farmer")


def _build_service():
    config = current_app.config
    weather_client = WeatherClient(
        provider=config.get("WEATHER_PROVIDER", "open_meteo"),
        latitude=config.get("WEATHER_LAT", 23.0225),
        longitude=config.get("WEATHER_LON", 72.5714),
        timeout_sec=config.get("WEATHER_TIMEOUT_SEC", 4),
    )
    return MarketIntelligenceService(
        MarketIntelligenceRepository(current_app.db),
        weather_client=weather_client,
        refresh_hours=config.get("AI_REFRESH_HOURS", 6),
        min_confidence=config.get("AI_MIN_CONFIDENCE", 70),
        min_trend_score=config.get("AI_MIN_TREND_SCORE", 65),
        model_version=config.get("AI_MODEL_VERSION", "ml-lite-v1"),
        model_store_path=config.get(
            "AI_MODEL_STORE_PATH",
            "artifacts/order_forecast_model.pkl",
        ),
        min_train_samples=config.get("AI_MIN_TRAIN_SAMPLES", 45),
        retrain_hours=config.get("AI_RETRAIN_HOURS", 24),
    )


def _handle_error(error):
    return jsonify({"error": error.message, "status": error.status_code}), error.status_code


@farmer_bp.get("/api/notifications")
def list_notifications_api():
    try:
        actor = extract_user_identity()
        data = _build_service().list_farmer_notifications(request.args, actor)
        return jsonify(data)
    except ServiceError as error:
        return _handle_error(error)


@farmer_bp.patch("/api/notifications/<notification_id>/read")
def read_notification_api(notification_id):
    try:
        actor = extract_user_identity()
        updated = _build_service().mark_notification_read(notification_id, actor)
        return jsonify({"item": updated})
    except ServiceError as error:
        return _handle_error(error)


def _extract_weather_payload(data):
    def _as_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _as_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    return {
        "temperature_c": _as_float((data or {}).get("temperature_c")),
        "condition": str((data or {}).get("condition") or "").strip(),
        "humidity": _as_int((data or {}).get("humidity")),
        "wind_speed": _as_float((data or {}).get("wind_speed")),
        "precipitation": _as_float((data or {}).get("precipitation")) or 0.0,
        "soil_type": str((data or {}).get("soil_type") or "loamy").strip() or "loamy",
        "location": str((data or {}).get("location") or "Gujarat").strip() or "Gujarat",
    }


@farmer_bp.route("/api/weather-suggestion", methods=["POST"])
@csrf.exempt
def weather_crop_suggestion():
    """Accept weather + soil input and return crop suggestions for farmer dashboard."""
    if not session.get("farmer_id"):
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    payload = _extract_weather_payload(request.get_json(silent=True) or {})
    month = datetime.datetime.now(datetime.timezone.utc).month

    suggestions = generate_weather_crop_suggestions(
        temperature_c=payload["temperature_c"],
        condition=payload["condition"],
        humidity=payload["humidity"],
        wind_speed=payload["wind_speed"],
        precipitation=payload["precipitation"],
        soil_type=payload["soil_type"],
        location=payload["location"],
        month=month,
    )

    return jsonify(
        {
            "success": True,
            "suggestions": suggestions,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    )


@farmer_bp.route("/api/ai-crop-suggestion", methods=["POST"])
@csrf.exempt
def ai_crop_suggestion():
    """Alias endpoint for UI clients that call ai-crop-suggestion directly."""
    return weather_crop_suggestion()


