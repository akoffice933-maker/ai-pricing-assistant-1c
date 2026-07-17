import { useState } from "react";
import SettingsBar from "./components/SettingsBar";
import PriceForm from "./components/PriceForm";
import ResultPanel from "./components/ResultPanel";
import { api, ApiError } from "./api";

export default function App() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(payload) {
    setLoading(true);
    setError(null);
    try {
      const data = await api.recommendPrice(payload);
      setResult(data);
    } catch (err) {
      setResult(null);
      if (err instanceof ApiError) {
        setError({ message: err.message, details: err.details });
      } else {
        setError({ message: "Непредвиденная ошибка. Проверьте консоль браузера." });
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-base">
      <header className="border-b border-line bg-panel/60 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <div className="font-display font-extrabold text-lg text-text tracking-tight">
              AI Pricing <span className="text-accentSoft">Assistant</span>
            </div>
            <div className="text-[11px] text-muted -mt-0.5">
              Рекомендация цены по рыночной кривой спроса — не прогноз, а расчёт
            </div>
          </div>
          <SettingsBar />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-6 items-start">
          <PriceForm onSubmit={handleSubmit} loading={loading} />
          <ResultPanel result={result} error={error} loading={loading} />
        </div>
      </main>

      <footer className="max-w-6xl mx-auto px-6 py-8 text-[11px] text-muted/60">
        Дашборд — тонкий клиент над FastAPI Skills Layer (тот же API, что использует 1С). Расчёты выполняются на backend.
      </footer>
    </div>
  );
}
