const STORAGE_KEY = "ai_pricing_dashboard_settings";

export function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { baseUrl: "http://localhost:8000", token: "" };
    return JSON.parse(raw);
  } catch {
    return { baseUrl: "http://localhost:8000", token: "" };
  }
}

export function saveSettings(settings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

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
  } catch (err) {
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
  forecastDemandCurve: (body) => request("/skills/forecast_demand_curve", { method: "POST", body }),
  calculateMarketIndicators: (body) =>
    request("/market/calculate_indicators", { method: "POST", body }),
};

export { ApiError };
