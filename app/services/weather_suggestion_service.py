"""Rule-based crop and farming suggestions from weather + soil signals."""

from __future__ import annotations

from typing import Any


CROP_RULES = [
    {
        "conditions": ["sunny", "clear"],
        "temp_range": (25, 42),
        "humidity_range": (20, 55),
        "crops": ["Cotton", "Groundnut", "Sunflower", "Jowar", "Bajra"],
        "action": "Ideal for sowing heat-tolerant crops. Irrigate early morning to reduce evaporation loss.",
        "soil_tips": {
            "sandy": "Add organic compost before sowing. Sandy soil dries fast in heat.",
            "loamy": "Excellent condition. Ensure furrow irrigation rows are prepared.",
            "clay": "Risk of surface cracking. Mulch the field to retain moisture.",
            "black": "Black soil retains heat. Perfect for cotton sowing this week.",
            "red": "Supplement with nitrogen fertilizer. Red soil low in nutrients.",
        },
        "warning": None,
    },
    {
        "conditions": ["rainy", "rain", "drizzle"],
        "temp_range": (18, 32),
        "humidity_range": (70, 100),
        "crops": ["Rice", "Maize", "Arhar", "Moong", "Ginger"],
        "action": "Good rainfall window. Prepare nursery beds for rice transplanting. Avoid pesticide spray.",
        "soil_tips": {
            "sandy": "Rain will drain quickly. Bund the field to retain water.",
            "loamy": "Perfect. Plant rice or maize in rows with 25cm spacing.",
            "clay": "Waterlogging risk. Create drainage channels immediately.",
            "black": "Black soil absorbs well. Ideal for arhar sowing in this rain.",
            "red": "Rain improves red soil moisture. Start maize sowing today.",
        },
        "warning": "Avoid spraying pesticides or fertilizers during active rainfall.",
    },
    {
        "conditions": ["cloudy", "overcast", "partly cloudy"],
        "temp_range": (20, 35),
        "humidity_range": (50, 80),
        "crops": ["Tomato", "Brinjal", "Cauliflower", "Wheat", "Mustard"],
        "action": "Overcast sky reduces water stress. Good time for transplanting seedlings.",
        "soil_tips": {
            "sandy": "Transplant with drip irrigation. Cloudy days reduce shock.",
            "loamy": "Ideal. Transplant tomato or brinjal seedlings in afternoon.",
            "clay": "Check soil moisture before transplanting. Avoid over-watering.",
            "black": "Good moisture retention. Plant mustard for excellent yield.",
            "red": "Use mulch after transplanting to retain soil moisture.",
        },
        "warning": None,
    },
    {
        "conditions": ["hot", "heatwave", "very hot"],
        "temp_range": (38, 50),
        "humidity_range": (10, 40),
        "crops": ["Bajra", "Jowar", "Moth Bean", "Cluster Bean"],
        "action": "Extreme heat advisory. Irrigate fields at dawn and dusk only. Avoid field work 11AM-4PM.",
        "soil_tips": {
            "sandy": "Critical: irrigate twice daily. Sandy soil loses moisture rapidly in heat.",
            "loamy": "Use sprinkler irrigation. Apply straw mulch 5cm thick.",
            "clay": "Clay soil may crack. Flood irrigate gently every 2 days.",
            "black": "Black soil handles heat well but water deeply every 3 days.",
            "red": "Highest risk. Add compost and irrigate daily in the morning.",
        },
        "warning": "Heat stress alert. Crops may wilt. Immediate irrigation recommended.",
    },
    {
        "conditions": ["windy", "strong wind"],
        "temp_range": (15, 38),
        "humidity_range": (20, 70),
        "crops": ["Wheat", "Barley", "Mustard", "Chickpea"],
        "action": "High wind conditions. Avoid spraying. Support tall crops with staking.",
        "soil_tips": {
            "sandy": "Wind erosion risk. Do not leave soil bare. Add windbreak crops on edges.",
            "loamy": "Moderate impact. Stake tall plants. Delay foliar spray.",
            "clay": "Minimal erosion risk from wind. Normal operations.",
            "black": "Black soil stable. Continue normal activities except spraying.",
            "red": "Red soil prone to wind erosion. Cover with crop residue.",
        },
        "warning": "Do not spray pesticides or fertilizers in high wind conditions.",
    },
]

DEFAULT_SUGGESTION = {
    "crops": ["Wheat", "Tomato", "Onion"],
    "action": "Weather data unavailable. Follow standard seasonal practices for your region.",
    "soil_tips": {},
    "warning": None,
}


def generate_weather_crop_suggestions(
    temperature_c: float | None,
    condition: str,
    humidity: int | None,
    wind_speed: float | None,
    precipitation: float | None,
    soil_type: str = "loamy",
    location: str = "",
    month: int = 1,
) -> list[dict[str, Any]]:
    """Return 3+ structured suggestion cards for current weather and soil."""
    condition_lower = (condition or "").lower()
    soil_lower = (soil_type or "loamy").lower()

    if temperature_c is not None and temperature_c >= 38:
        condition_lower = "hot"

    matched = None
    for rule in CROP_RULES:
        for keyword in rule["conditions"]:
            if keyword in condition_lower:
                t_min, t_max = rule["temp_range"]
                if temperature_c is None or t_min <= temperature_c <= t_max:
                    matched = rule
                    break
        if matched:
            break

    if not matched:
        matched = DEFAULT_SUGGESTION

    soil_tip = matched.get("soil_tips", {}).get(
        soil_lower,
        "Maintain adequate soil moisture for the current weather conditions.",
    )

    temp_detail = f"{float(temperature_c):.1f}degC" if temperature_c is not None else "unknown temperature"
    humidity_detail = f"{int(humidity)}% humidity" if humidity is not None else "unknown humidity"

    suggestions = [
        {
            "type": "crops",
            "title": "Recommended Crops",
            "icon": "sprout",
            "body": ", ".join(matched["crops"]),
            "detail": f"Best suited for current {condition or 'variable'} weather in {location or 'your location'}.",
            "color": "green",
        },
        {
            "type": "action",
            "title": "Farming Action",
            "icon": "shovel",
            "body": matched["action"],
            "detail": f"Based on {temp_detail} and {humidity_detail}.",
            "color": "blue",
        },
        {
            "type": "soil",
            "title": f"Soil Tip ({(soil_type or 'Loamy').title()} Soil)",
            "icon": "layers",
            "body": soil_tip,
            "detail": "Adjust irrigation and amendment schedules accordingly.",
            "color": "amber",
        },
    ]

    if matched.get("warning"):
        suggestions.append(
            {
                "type": "warning",
                "title": "Advisory",
                "icon": "triangle-alert",
                "body": matched["warning"],
                "detail": "Take precautionary action to protect your crops.",
                "color": "red",
            }
        )

    return suggestions

