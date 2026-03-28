/* Krishi Connect — Weather + AI Suggestion Widget */

const WMO_CODES = {
  0: { label: "Clear Sky", icon: "sun", color: "#f59e0b" },
  1: { label: "Mainly Clear", icon: "sun", color: "#f59e0b" },
  2: { label: "Partly Cloudy", icon: "cloud-sun", color: "#6b7280" },
  3: { label: "Overcast", icon: "cloud", color: "#6b7280" },
  45: { label: "Foggy", icon: "cloud-fog", color: "#9ca3af" },
  48: { label: "Icy Fog", icon: "cloud-fog", color: "#9ca3af" },
  51: { label: "Light Drizzle", icon: "cloud-drizzle", color: "#0891b2" },
  53: { label: "Drizzle", icon: "cloud-drizzle", color: "#0891b2" },
  55: { label: "Heavy Drizzle", icon: "cloud-drizzle", color: "#0891b2" },
  61: { label: "Light Rain", icon: "cloud-rain", color: "#2563eb" },
  63: { label: "Rain", icon: "cloud-rain", color: "#2563eb" },
  65: { label: "Heavy Rain", icon: "cloud-rain", color: "#1d4ed8" },
  71: { label: "Light Snow", icon: "cloud-snow", color: "#93c5fd" },
  73: { label: "Snow", icon: "cloud-snow", color: "#93c5fd" },
  80: { label: "Rain Showers", icon: "cloud-rain", color: "#2563eb" },
  95: { label: "Thunderstorm", icon: "cloud-lightning", color: "#7c3aed" },
  99: { label: "Severe Storm", icon: "cloud-lightning", color: "#7c3aed" },
};

function getWeatherMeta(code) {
  return WMO_CODES[code] || { label: "Variable", icon: "cloud-sun", color: "#6b7280" };
}

function displayTemp(celsius) {
  const value = Number(celsius);
  if (!Number.isFinite(value)) return "--";
  return `${Math.round(value)}degC`;
}

function createIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

let currentWeatherData = null;

async function initWeather() {
  const loading = document.getElementById("weatherLoading");
  const error = document.getElementById("weatherError");
  const content = document.getElementById("weatherContent");
  if (!loading || !error || !content) return;

  loading.classList.remove("hidden");
  error.classList.add("hidden");
  content.classList.add("hidden");

  try {
    const pos = await new Promise((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        timeout: 10000,
        maximumAge: 300000,
      })
    );

    const { latitude: lat, longitude: lon } = pos.coords;

    let locationName = "Your Location";
    try {
      const geoRes = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
        { headers: { "Accept-Language": "en" } }
      );
      const geoData = await geoRes.json();
      const addr = geoData.address || {};
      locationName =
        addr.city ||
        addr.town ||
        addr.village ||
        addr.county ||
        addr.state_district ||
        addr.state ||
        "Your Location";
    } catch (errorLocation) {
      console.warn("Location name lookup skipped:", errorLocation);
    }

    const locationText = document.getElementById("locationText");
    if (locationText) locationText.textContent = locationName;

    const weatherUrl =
      "https://api.open-meteo.com/v1/forecast?" +
      `latitude=${lat}&longitude=${lon}` +
      "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m" +
      "&daily=weather_code,temperature_2m_max,precipitation_sum,precipitation_probability_max" +
      "&timezone=auto" +
      "&forecast_days=4";

    const weatherRes = await fetch(weatherUrl);
    const weatherData = await weatherRes.json();

    const current = weatherData.current || {};
    const daily = weatherData.daily || {};

    currentWeatherData = {
      temperature_c: current.temperature_2m,
      humidity: current.relative_humidity_2m,
      precipitation: current.precipitation,
      wind_speed: current.wind_speed_10m,
      weather_code: current.weather_code,
      location: locationName,
      lat,
      lon,
    };

    const meta = getWeatherMeta(current.weather_code);

    const setText = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value;
    };

    setText("cwTemp", displayTemp(current.temperature_2m));
    setText("cwCondition", meta.label);
    setText("cwLocation", locationName);
    setText("cwHumidity", `${current.relative_humidity_2m ?? "--"}%`);
    setText("cwWind", `${current.wind_speed_10m ?? "--"} km/h`);
    setText("cwRain", `${current.precipitation ?? "--"} mm`);
    setText("cwUpdated", "just now");

    const mainIcon = document.getElementById("cwMainIcon");
    if (mainIcon) {
      mainIcon.setAttribute("data-lucide", meta.icon);
      mainIcon.style.color = "#fde68a";
    }

    const forecastContainer = document.getElementById("forecastCards");
    if (forecastContainer) {
      forecastContainer.innerHTML = "";
      const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
      for (let i = 1; i <= 3; i += 1) {
        const dateStr = (daily.time || [])[i];
        if (!dateStr) continue;
        const d = new Date(`${dateStr}T00:00:00`);
        const dayLabel = dayNames[d.getDay()];
        const dateDisp = d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
        const fMeta = getWeatherMeta((daily.weather_code || [])[i]);
        const tempMax = Math.round(Number((daily.temperature_2m_max || [])[i] ?? 0));
        const rainProb = Number((daily.precipitation_probability_max || [])[i] ?? 0);
        const rainAmt = Number((daily.precipitation_sum || [])[i] ?? 0).toFixed(1);

        forecastContainer.insertAdjacentHTML(
          "beforeend",
          `
          <div class="forecast-card">
            <div class="fc-day">${dayLabel}</div>
            <div class="fc-date">${dateDisp}</div>
            <div class="fc-icon"><i data-lucide="${fMeta.icon}" style="color:${fMeta.color}"></i></div>
            <div class="fc-temp">${tempMax}degC</div>
            <div class="fc-cond">${escapeHtml(fMeta.label)}</div>
            ${rainProb > 0 ? `<div class="fc-rain"><i data-lucide="droplets"></i>${rainProb}% · ${rainAmt}mm</div>` : ""}
          </div>
          `
        );
      }
    }

    loading.classList.add("hidden");
    content.classList.remove("hidden");
    createIcons();

    await fetchAISuggestions();
  } catch (errorWeather) {
    console.error("Weather widget error:", errorWeather);
    loading.classList.add("hidden");
    error.classList.remove("hidden");
    createIcons();
  }
}

async function fetchAISuggestions() {
  if (!currentWeatherData) return;

  const soilType = document.getElementById("soilType")?.value || "loamy";
  const loadBadge = document.getElementById("aiLoadingBadge");
  const aiBadge = document.getElementById("aiBadge");
  const grid = document.getElementById("suggestionGrid");
  if (!grid) return;

  loadBadge?.classList.remove("hidden");
  aiBadge?.classList.add("hidden");
  grid.innerHTML = '<div style="padding:24px;color:#6b7280;font-size:0.875rem;">Generating suggestions...</div>';

  try {
    const response = await fetch("/farmer/api/ai-crop-suggestion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        temperature_c: currentWeatherData.temperature_c,
        condition: getWeatherMeta(currentWeatherData.weather_code).label,
        humidity: currentWeatherData.humidity,
        wind_speed: currentWeatherData.wind_speed,
        precipitation: currentWeatherData.precipitation,
        soil_type: soilType,
        location: currentWeatherData.location,
      }),
    });

    const data = await response.json();
    renderSuggestions(data.suggestions || []);
  } catch (errorSuggestion) {
    grid.innerHTML = '<div style="padding:24px;color:#dc2626;font-size:0.875rem;">Could not load suggestions. Check your connection.</div>';
  } finally {
    loadBadge?.classList.add("hidden");
    aiBadge?.classList.remove("hidden");
    createIcons();
  }
}

function renderSuggestions(suggestions) {
  const grid = document.getElementById("suggestionGrid");
  if (!grid) return;
  grid.innerHTML = "";

  suggestions.forEach((item, idx) => {
    if (item.type === "warning") {
      grid.insertAdjacentHTML(
        "beforeend",
        `
        <div class="sc-warning" style="animation-delay:${idx * 80}ms">
          <i data-lucide="triangle-alert"></i>
          <div>
            <div style="font-weight:700;margin-bottom:4px;">${escapeHtml(item.title || "Advisory")}</div>
            ${escapeHtml(item.body || "")}
          </div>
        </div>
        `
      );
      return;
    }

    grid.insertAdjacentHTML(
      "beforeend",
      `
      <div class="suggestion-card" style="animation-delay:${idx * 80}ms">
        <div class="sc-header">
          <div class="sc-icon ${escapeHtml(item.color || "green")}">
            <i data-lucide="${escapeHtml(item.icon || "sprout")}"></i>
          </div>
          <div class="sc-title">${escapeHtml(item.title || "Suggestion")}</div>
        </div>
        <div class="sc-body">${escapeHtml(item.body || "")}</div>
        <div class="sc-detail">${escapeHtml(item.detail || "")}</div>
      </div>
      `
    );
  });

  createIcons();
}

document.addEventListener("DOMContentLoaded", () => {
  const soilSelect = document.getElementById("soilType");
  if (soilSelect) {
    soilSelect.addEventListener("change", fetchAISuggestions);
  }
  initWeather();
});


