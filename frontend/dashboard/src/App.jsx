import { useState } from "react";
import { Terminal } from "lucide-react";
import SettingsBar from "./components/SettingsBar";
import PriceForm from "./components/PriceForm";
import ResultPanel from "./components/ResultPanel";
import { api, ApiError } from "./api";

function Background() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-ink" />
      <div className="absolute inset-0 bg-grid" />
      <div
        className="absolute -top-40 left-1/2 h-[560px] w-[900px] -translate-x-1/2 rounded-full opacity-[0.10] blur-[130px]"
        style={{ background: "radial-gradient(closest-side, #d7ff3f, transparent)" }}
      />
      <div
        className="absolute right-[-200px] top-[35%] h-[500px] w-[500px] rounded-full opacity-[0.06] blur-[120px]"
        style={{ background: "radial-gradient(closest-side, #6fd3ff, transparent)" }}
      />
    </div>
  );
}

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
    <div className="min-h-screen">
      <Background />

      <header className="border-b border-line/70 bg-ink/75 backdrop-blur-xl sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-lg border border-line bg-panel text-lime">
              <Terminal size={16} strokeWidth={2.2} />
            </span>
            <div>
              <div className="font-mono text-[11px] leading-tight tracking-[0.15em] text-mist">
                AI_PRICING_ASSISTANT
              </div>
              <div className="text-[11px] text-fog -mt-0.5">
                Рекомендация цены по рыночной кривой спроса
              </div>
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

      <footer className="max-w-6xl mx-auto px-6 py-8 font-mono text-[10px] tracking-[0.1em] text-fog/70">
        ДАШБОРД — ТОНКИЙ КЛИЕНТ НАД FASTAPI SKILLS LAYER. РАСЧЁТЫ ВЫПОЛНЯЮТСЯ НА BACKEND.
      </footer>
    </div>
  );
}
