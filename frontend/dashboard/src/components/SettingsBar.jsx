import { useEffect, useState } from "react";
import { loadSettings, saveSettings, api, isLocalBaseUrl } from "../api";
import { TextInput, Pill } from "./ui";

export default function SettingsBar() {
  const [open, setOpen] = useState(false);
  const [settings, setSettings] = useState(loadSettings());
  const [status, setStatus] = useState("unknown"); // unknown | ok | degraded | error

  async function checkConnection() {
    setStatus("checking");
    try {
      const res = await api.ready();
      setStatus(res.status === "ok" ? "ok" : "degraded");
    } catch {
      setStatus("error");
    }
  }

  useEffect(() => {
    checkConnection();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSave(e) {
    e.preventDefault();
    saveSettings(settings);
    setOpen(false);
    checkConnection();
  }

  const statusTone = { ok: "good", degraded: "warn", error: "bad", checking: "neutral", unknown: "neutral" }[status];
  const statusLabel = {
    ok: "Подключено",
    degraded: "Подключено, требует внимания",
    error: "Нет связи с сервисом",
    checking: "Проверка…",
    unknown: "—",
  }[status];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 text-xs text-muted hover:text-text transition-colors focus-ring outline-none rounded-md px-2 py-1"
      >
        <span className={`w-1.5 h-1.5 rounded-full ${statusTone === "good" ? "bg-good" : statusTone === "bad" ? "bg-bad" : statusTone === "warn" ? "bg-warn" : "bg-muted"}`} />
        {statusLabel}
        <span className="text-muted/60">· настройки</span>
      </button>

      {open && (
        <form
          onSubmit={handleSave}
          className="absolute right-0 top-8 z-20 w-80 bg-panel2 border border-line rounded-xl p-4 shadow-2xl"
        >
          <div className="mb-3">
            <div className="text-xs font-medium text-muted mb-1">Адрес backend-сервиса</div>
            <TextInput
              value={settings.baseUrl}
              onChange={(e) => setSettings({ ...settings, baseUrl: e.target.value })}
              placeholder="http://localhost:8000"
            />
          </div>
          <div className="mb-4">
            <div className="text-xs font-medium text-muted mb-1">API-токен (Bearer)</div>
            <TextInput
              type="password"
              value={settings.token}
              onChange={(e) => setSettings({ ...settings, token: e.target.value })}
              placeholder="Оставьте пустым, если auth отключён на сервере"
            />
          </div>
          <div className="flex items-center justify-between">
            <Pill tone={statusTone}>{statusLabel}</Pill>
            <button
              type="submit"
              className="bg-accent text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-accentSoft transition-colors"
            >
              Сохранить
            </button>
          </div>
          <p className="text-[11px] text-muted/70 mt-3 leading-relaxed">
            {isLocalBaseUrl(settings.baseUrl)
              ? "Токен хранится в этом браузере (localStorage) и отправляется напрямую в ваш backend."
              : "Backend не локальный — токен НЕ сохраняется на диск (только в памяти этой вкладки, " +
                "исчезнет при перезагрузке страницы). Это снижает риск кражи токена через XSS на странице дашборда."}
          </p>
        </form>
      )}
    </div>
  );
}
