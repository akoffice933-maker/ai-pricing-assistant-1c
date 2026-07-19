import { Suspense, lazy, useState } from "react";
import { Terminal, TrendingUp, LineChart, Scale, Layers, Calculator } from "lucide-react";
import SettingsBar from "./components/SettingsBar";
import PriceForm from "./components/PriceForm";
import ResultPanel from "./components/ResultPanel";
import { api, ApiError } from "./api";
import { DEMO_RESULT } from "./lib/demoData";

// Ленивая загрузка: эти вкладки не нужны при первом заходе (по умолчанию открыта
// «Рекомендация»), не тянем их код и recharts-зависимости в основной бандл.
const GoalComparePage = lazy(() => import("./components/GoalComparePage"));
const MarketIndicatorsPage = lazy(() => import("./components/MarketIndicatorsPage"));
const BatchPage = lazy(() => import("./components/BatchPage"));
const RoiCalculatorPage = lazy(() => import("./components/RoiCalculatorPage"));

const TABS = [
  { key: "recommend", label: "Рекомендация", icon: TrendingUp },
  { key: "market", label: "Рыночные индикаторы", icon: LineChart },
  { key: "compare", label: "Сравнение целей", icon: Scale },
  { key: "batch", label: "Пакетный расчёт", icon: Layers },
  { key: "roi", label: "ROI", icon: Calculator },
];

function TabFallback() {
  return <div className="text-fog text-sm py-12 text-center">Загрузка…</div>;
}

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

function Nav({ tab, setTab }) {
  return (
    <nav className="flex items-center gap-1 border border-line rounded-lg bg-panel p-1">
      {TABS.map((t) => {
        const Icon = t.icon;
        const active = tab === t.key;
        return (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors focus-ring outline-none ${
              active ? "bg-lime text-ink" : "text-mist hover:text-text"
            }`}
          >
            <Icon size={13} strokeWidth={2.2} />
            {t.label}
          </button>
        );
      })}
    </nav>
  );
}

function RecommendTab() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isDemo, setIsDemo] = useState(false);

  async function handleSubmit(payload) {
    setLoading(true);
    setError(null);
    setIsDemo(false);
    try {
      const data = await api.recommendPrice(payload);
      setResult(data);
    } catch (err) {
      setResult(null);
      if (err instanceof ApiError) {
        setError({ message: err.message, details: err.details, isConnectionError: err.status === 0 });
      } else {
        setError({ message: "Непредвиденная ошибка. Проверьте консоль браузера." });
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function showDemo() {
    setError(null);
    setResult(DEMO_RESULT);
    setIsDemo(true);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs text-fog max-w-lg">
          Backend не задеплоен на GitHub Pages — только статика. Чтобы посчитать реальную
          рекомендацию, запустите backend локально (см. настройки справа сверху) — либо
          посмотрите демо на примере из <code className="text-mist">examples/product_recommend_price.json</code>.
        </p>
        <button
          onClick={showDemo}
          className="shrink-0 ml-4 text-xs font-mono text-lime hover:text-limedim transition-colors border border-lime/30 rounded-md px-3 py-1.5"
        >
          Показать демо
        </button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-6 items-start">
        <PriceForm onSubmit={handleSubmit} loading={loading} />
        <ResultPanel result={result} error={error} loading={loading} isDemo={isDemo} onShowDemo={showDemo} />
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("recommend");

  return (
    <div className="min-h-screen">
      <Background />

      <header className="border-b border-line/70 bg-ink/75 backdrop-blur-xl sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
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
          <Nav tab={tab} setTab={setTab} />
          <SettingsBar />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        {tab === "recommend" && <RecommendTab />}
        <Suspense fallback={<TabFallback />}>
          {tab === "market" && <MarketIndicatorsPage />}
          {tab === "compare" && <GoalComparePage />}
          {tab === "batch" && <BatchPage />}
          {tab === "roi" && <RoiCalculatorPage />}
        </Suspense>
      </main>

      <footer className="max-w-6xl mx-auto px-6 py-8 font-mono text-[10px] tracking-[0.1em] text-fog/70">
        ДАШБОРД — ТОНКИЙ КЛИЕНТ НАД FASTAPI SKILLS LAYER. РАСЧЁТЫ ВЫПОЛНЯЮТСЯ НА BACKEND.
      </footer>
    </div>
  );
}
