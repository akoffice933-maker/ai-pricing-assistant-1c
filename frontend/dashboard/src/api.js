const STORAGE_KEY = "ai_pricing_dashboard_settings";

// In-memory copy — источник истины на время жизни вкладки. localStorage используется
// только как персистентный кэш для localhost-backend (см. saveSettings).
let memorySettings = null;

function isLocalBaseUrl(baseUrl) {
  try {
    const { hostname } = new URL(baseUrl);
    return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "[::1]";
  } catch {
    return false;
  }
}

export function loadSettings() {
  if (memorySettings) return memorySettings;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    memorySettings = raw ? JSON.parse(raw) : { baseUrl: "http://localhost:8000", token: "" };
  } catch {
    memorySettings = { baseUrl: "http://localhost:8000", token: "" };
  }
  return memorySettings;
}

export function saveSettings(settings) {
  // Токен всегда доступен в памяти на время текущей вкладки (нужен для реальных запросов).
  memorySettings = settings;
  // На диск (localStorage, переживает перезагрузку страницы) токен пишем только если
  // backend локальный. Если указан не-localhost backend — на диск сохраняем всё, кроме
  // токена, чтобы снизить ущерб от возможной XSS-атаки на страницу дашборда: после
  // перезагрузки страницы токен придётся ввести заново, но во время сессии он работает.
  const toPersist = isLocalBaseUrl(settings.baseUrl) ? settings : { ...settings, token: "" };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(toPersist));
}

export { isLocalBaseUrl };

class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

async function request(path, { method = "GET", body } = {}) {
  const { baseUrl, token } = loadSettings();
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(
      `Не удалось подключиться к ${baseUrl}. Проверьте, что сервис запущен и адрес указан верно.`,
      0,
      null
    );
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    // тело ответа могло быть пустым
  }

  if (!response.ok) {
    if (response.status === 401) {
      throw new ApiError("Неверный или отсутствующий API-токен.", 401, payload);
    }
    if (response.status === 422) {
      throw new ApiError(
        payload?.detail || "Некорректные входные данные.",
        422,
        payload?.errors
      );
    }
    if (response.status === 429) {
      throw new ApiError("Превышен лимит запросов. Попробуйте через минуту.", 429, payload);
    }
    throw new ApiError(
      payload?.detail || `Ошибка сервера (${response.status}).`,
      response.status,
      payload
    );
  }

  return payload;
}

export const api = {
  health: () => request("/health"),
  ready: () => request("/ready"),
  recommendPrice: (body) => request("/skills/recommend_price", { method: "POST", body }),
  recommendPriceBatch: (body) => request("/skills/recommend_price/batch", { method: "POST", body }),
  forecastDemandCurve: (body) => request("/skills/forecast_demand_curve", { method: "POST", body }),
  calculateMarketIndicators: (body) =>
    request("/market/calculate_indicators", { method: "POST", body }),
};

export { ApiError };
