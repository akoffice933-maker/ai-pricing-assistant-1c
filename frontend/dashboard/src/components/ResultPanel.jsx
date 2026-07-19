import { Suspense, lazy } from "react";
import { Card, Pill } from "./ui";

const DemandCurveChart = lazy(() => import("./DemandCurveChart"));

function ChartFallback() {
  return <div className="h-64 flex items-center justify-center text-fog text-xs">Загрузка графика…</div>;
}

function fmt(n, digits = 0) {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("ru-RU", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export default function ResultPanel({ result, error, loading, isDemo = false, onShowDemo }) {
  if (loading) {
    return (
      <Card>
        <div className="text-muted text-sm py-12 text-center">Считаем рекомендацию…</div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Не удалось получить рекомендацию">
        <p className="text-bad text-sm mb-2">{error.message}</p>
        {Array.isArray(error.details) && (
          <ul className="text-xs text-muted space-y-1 list-disc list-inside">
            {error.details.map((d, i) => (
              <li key={i}>{(d.loc || []).join(" → ")}: {d.msg}</li>
            ))}
          </ul>
        )}
        {error.isConnectionError && onShowDemo && (
          <button
            onClick={onShowDemo}
            className="mt-3 text-xs font-mono text-lime hover:text-limedim transition-colors border border-lime/30 rounded-md px-3 py-1.5"
          >
            Показать демо вместо этого
          </button>
        )}
      </Card>
    );
  }

  if (!result) {
    return (
      <Card>
        <div className="text-muted text-sm py-12 text-center">
          Заполните форму слева и нажмите «Рассчитать рекомендацию»
        </div>
      </Card>
    );
  }

  const changeSign = result.price_change_percent > 0 ? "+" : "";
  const changeTone = result.price_change_percent > 0 ? "good" : result.price_change_percent < 0 ? "bad" : "neutral";

  return (
    <div className="space-y-4">
      {isDemo && (
        <div className="flex items-center gap-2 bg-warn/10 border border-warn/30 rounded-lg px-3 py-2">
          <Pill tone="warn">Демо</Pill>
          <span className="text-xs text-mist">
            Это сохранённый пример ответа, а не живой расчёт — backend недоступен.
          </span>
        </div>
      )}
      <Card>
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs text-muted mb-1">{result.item_name}</div>
            <div className="flex items-baseline gap-2">
              <span className="font-display font-extrabold text-4xl text-text tracking-tight">
                {fmt(result.recommended_price, 2)}
              </span>
              <span className="text-muted text-sm">{result.currency} / {result.price_unit}</span>
            </div>
            <div className="text-xs text-muted mt-1">
              было {fmt(result.current_price, 2)} · <span className={changeTone === "good" ? "text-good" : changeTone === "bad" ? "text-bad" : "text-muted"}>{changeSign}{fmt(result.price_change_percent, 1)}%</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <Pill tone={result.is_reliable ? "good" : "warn"}>
              {result.is_reliable ? "Можно применять автоматически" : "Требует согласования"}
            </Pill>
            <span className="text-[11px] text-muted">confidence {fmt(result.confidence * 100, 0)}%</span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 mt-5 pt-4 border-t border-line">
          <div>
            <div className="text-[11px] text-muted">Ожид. спрос</div>
            <div className="text-sm font-semibold text-text">{fmt(result.expected_demand, 1)}</div>
          </div>
          <div>
            <div className="text-[11px] text-muted">Ожид. выручка</div>
            <div className="text-sm font-semibold text-text">{fmt(result.expected_revenue, 0)}</div>
          </div>
          <div>
            <div className="text-[11px] text-muted">Маржа</div>
            <div className="text-sm font-semibold text-text">{fmt(result.expected_margin_percent, 1)}%</div>
          </div>
        </div>
      </Card>

      <Card title="Кривая спроса" subtitle="Цена → ожидаемый спрос; закрашена зона допустимых цен">
        <Suspense fallback={<ChartFallback />}>
          <DemandCurveChart
            curve={result.demand_curve}
            recommendedPrice={result.recommended_price}
            currentPrice={result.current_price}
            bounds={result.price_bounds}
          />
        </Suspense>
      </Card>

      {result.warnings?.length > 0 && (
        <Card className="border-warn/30">
          <div className="text-xs font-semibold text-warn mb-2">Предупреждения</div>
          <ul className="space-y-1.5">
            {result.warnings.map((w, i) => (
              <li key={i} className="text-xs text-text/90 flex gap-2">
                <span className="text-warn">▲</span>
                <span>{w}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card title="Объяснение">
        <ul className="space-y-1.5 mb-3">
          {result.explanation?.summary?.map((s, i) => (
            <li key={i} className="text-xs text-text/90">· {s}</li>
          ))}
        </ul>
        <div className="grid grid-cols-1 gap-2 text-xs">
          {result.explanation?.positive_factors?.map((s, i) => (
            <div key={`p${i}`} className="flex gap-2"><span className="text-good">+</span><span className="text-muted">{s}</span></div>
          ))}
          {result.explanation?.negative_factors?.map((s, i) => (
            <div key={`n${i}`} className="flex gap-2"><span className="text-bad">−</span><span className="text-muted">{s}</span></div>
          ))}
        </div>
      </Card>
    </div>
  );
}
