import { useState } from "react";
import { Card, Field, TextInput, NumberInput, Button } from "./ui";
import { api, ApiError } from "../api";

function num(v) {
  return v === "" || v === null || v === undefined ? null : Number(v);
}

function newObservation() {
  return { price: "", competitor_id: "", is_promo: false, is_available: true };
}

function fmt(n, digits = 2) {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("ru-RU", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export default function MarketIndicatorsPage() {
  const [category, setCategory] = useState("wireless_headphones");
  const [region, setRegion] = useState("");
  const [channel, setChannel] = useState("");
  const [observations, setObservations] = useState([newObservation(), newObservation(), newObservation()]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function updateObservation(index, patch) {
    setObservations((obs) => obs.map((o, i) => (i === index ? { ...o, ...patch } : o)));
  }

  function addObservation() {
    setObservations((obs) => [...obs, newObservation()]);
  }

  function removeObservation(index) {
    setObservations((obs) => obs.filter((_, i) => i !== index));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = {
        market_category: category,
        ...(region ? { region } : {}),
        ...(channel ? { channel } : {}),
        observations: observations
          .filter((o) => o.price !== "")
          .map((o) => ({
            price: num(o.price),
            competitor_id: o.competitor_id || undefined,
            is_promo: !!o.is_promo,
            is_available: !!o.is_available,
          })),
      };
      const data = await api.calculateMarketIndicators(payload);
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Непредвиденная ошибка.");
    } finally {
      setLoading(false);
    }
  }

  const ctx = result?.market_context;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-6 items-start">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Card title="Категория рынка">
          <div className="grid grid-cols-2 gap-x-3">
            <Field label="Категория">
              <TextInput value={category} onChange={(e) => setCategory(e.target.value)} required />
            </Field>
            <Field label="Регион" hint="опционально">
              <TextInput value={region} onChange={(e) => setRegion(e.target.value)} placeholder="LV, RU-77…" />
            </Field>
            <Field label="Канал" hint="опционально">
              <TextInput value={channel} onChange={(e) => setChannel(e.target.value)} placeholder="online, retail…" />
            </Field>
          </div>
        </Card>

        <Card title="Наблюдения конкурентов" subtitle="Цена + признаки промо/наличия по каждому конкуренту">
          <div className="space-y-3">
            {observations.map((o, i) => (
              <div key={i} className="border border-line rounded-lg p-3 bg-panel2">
                <div className="grid grid-cols-2 gap-x-3 gap-y-2">
                  <Field label="Цена">
                    <NumberInput step="0.01" value={o.price} onChange={(e) => updateObservation(i, { price: e.target.value })} />
                  </Field>
                  <Field label="ID конкурента">
                    <TextInput value={o.competitor_id} onChange={(e) => updateObservation(i, { competitor_id: e.target.value })} />
                  </Field>
                </div>
                <div className="flex items-center gap-4 mt-2">
                  <label className="flex items-center gap-1.5 text-xs text-mist">
                    <input type="checkbox" checked={o.is_promo} onChange={(e) => updateObservation(i, { is_promo: e.target.checked })} className="accent-lime" />
                    промо
                  </label>
                  <label className="flex items-center gap-1.5 text-xs text-mist">
                    <input type="checkbox" checked={o.is_available} onChange={(e) => updateObservation(i, { is_available: e.target.checked })} className="accent-lime" />
                    в наличии
                  </label>
                  {observations.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeObservation(i)}
                      className="ml-auto text-[11px] text-fog hover:text-danger transition-colors"
                    >
                      удалить
                    </button>
                  )}
                </div>
              </div>
            ))}
            <button
              type="button"
              onClick={addObservation}
              className="text-xs text-lime hover:text-limedim transition-colors font-mono"
            >
              + добавить наблюдение
            </button>
          </div>
        </Card>

        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Считаем…" : "Рассчитать индикаторы"}
        </Button>
      </form>

      <div className="space-y-4">
        {!result && !error && !loading && (
          <Card>
            <div className="text-fog text-sm py-12 text-center">
              Добавьте наблюдения слева — получите нормализованный market_context, готовый
              для передачи в форму рекомендации или для выгрузки в 1С.
            </div>
          </Card>
        )}

        {error && (
          <Card title="Ошибка">
            <p className="text-danger text-sm">{error}</p>
          </Card>
        )}

        {ctx && (
          <>
            <Card title="market_context">
              <div className="grid grid-cols-3 gap-4">
                <Stat label="Медиана" value={fmt(ctx.market_price_median)} />
                <Stat label="p25 / p75" value={`${fmt(ctx.market_price_p25)} / ${fmt(ctx.market_price_p75)}`} />
                <Stat label="Min / Max" value={`${fmt(ctx.market_price_min)} / ${fmt(ctx.market_price_max)}`} />
                <Stat label="Конкурентов" value={fmt(ctx.competitor_count, 0)} />
                <Stat label="Активных" value={fmt(ctx.active_competitor_count, 0)} />
                <Stat label="Доля промо" value={`${fmt(ctx.promo_share * 100, 0)}%`} />
                <Stat label="Доступность" value={`${fmt(ctx.availability_index * 100, 0)}%`} />
                <Stat label="Confidence" value={`${fmt(ctx.confidence * 100, 0)}%`} />
                <Stat label="Индекс спроса" value={fmt(ctx.market_demand_index)} />
              </div>
            </Card>
            <Card title="Готово для 1С" subtitle="POST /market/calculate_indicators/export_1c вернёт такую же запись">
              <pre className="text-[11px] font-mono text-mist bg-panel2 border border-line rounded-lg p-3 overflow-x-auto">
                {JSON.stringify(result.one_c_indicator_record ?? ctx, null, 2)}
              </pre>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-fog mb-0.5">{label}</div>
      <div className="text-sm font-semibold text-text">{value}</div>
    </div>
  );
}
