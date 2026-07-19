import { useState } from "react";
import { Card, Button, Pill } from "./ui";
import { defaultItem, defaultMarket } from "../lib/defaults";
import { api, ApiError } from "../api";

function fmt(n, digits = 2) {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("ru-RU", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function sampleItems() {
  const base = { business_goal: "maximize_profit", item: defaultItem(), market_context: defaultMarket() };
  const second = {
    business_goal: "clear_stock",
    item: { ...defaultItem(), item_id: "000000456", item_name: "Наушники X200 (склад Б)", stock_quantity: 12 },
    market_context: defaultMarket(),
  };
  return JSON.stringify([base, second], null, 2);
}

export default function BatchPage() {
  const [text, setText] = useState(sampleItems());
  const [parseError, setParseError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setParseError(null);
    setError(null);
    setResponse(null);

    let items;
    try {
      items = JSON.parse(text);
      if (!Array.isArray(items)) throw new Error("Ожидается JSON-массив объектов.");
    } catch (err) {
      setParseError(err.message);
      return;
    }

    setLoading(true);
    try {
      const data = await api.recommendPriceBatch({ items });
      setResponse(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Непредвиденная ошибка.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[480px_1fr] gap-6 items-start">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Card
          title="Пакет позиций"
          subtitle="JSON-массив объектов {business_goal, item, market_context} — до 200 штук"
        >
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            spellCheck={false}
            rows={18}
            className="w-full bg-panel2 border border-line rounded-lg px-3 py-2 text-xs font-mono text-text focus-ring outline-none focus:border-lime/50"
          />
          {parseError && <p className="text-danger text-xs mt-2">Некорректный JSON: {parseError}</p>}
        </Card>
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Считаем пакет…" : "Рассчитать пакет"}
        </Button>
      </form>

      <div className="space-y-4">
        {!response && !error && !loading && (
          <Card>
            <div className="text-fog text-sm py-12 text-center">
              Отредактируйте JSON слева (или оставьте пример) и нажмите «Рассчитать пакет».
              Некорректная позиция не роняет весь пакет — попадёт в таблицу с пометкой ошибки.
            </div>
          </Card>
        )}

        {error && (
          <Card title="Ошибка">
            <p className="text-danger text-sm">{error}</p>
          </Card>
        )}

        {response && (
          <>
            <Card>
              <div className="flex items-center gap-4">
                <Stat label="Всего" value={response.total} />
                <Stat label="Успешно" value={response.succeeded} tone="good" />
                <Stat label="Ошибок" value={response.failed} tone={response.failed > 0 ? "bad" : "neutral"} />
              </div>
            </Card>
            <Card title="Результаты" className="!p-0 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="font-mono text-[10px] uppercase tracking-[0.1em] text-fog border-b border-line">
                    <th className="text-left px-4 py-2.5">#</th>
                    <th className="text-left px-4 py-2.5">Позиция</th>
                    <th className="text-right px-4 py-2.5">Цена</th>
                    <th className="text-right px-4 py-2.5">Спрос</th>
                    <th className="text-right px-4 py-2.5">Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {response.results.map((r) => (
                    <tr key={r.index} className="border-b border-line/50 last:border-0">
                      <td className="px-4 py-2.5 text-fog font-mono text-xs">{r.index}</td>
                      <td className="px-4 py-2.5 text-text">{r.item_id ?? "—"}</td>
                      {r.ok ? (
                        <>
                          <td className="px-4 py-2.5 text-right font-display font-semibold text-text">
                            {fmt(r.result.recommended_price)}
                          </td>
                          <td className="px-4 py-2.5 text-right text-mist">{fmt(r.result.expected_demand, 1)}</td>
                          <td className="px-4 py-2.5 text-right">
                            <Pill tone={r.result.is_reliable ? "good" : "warn"}>
                              {r.result.is_reliable ? "OK" : "Review"}
                            </Pill>
                          </td>
                        </>
                      ) : (
                        <td className="px-4 py-2.5 text-danger text-xs" colSpan={3}>{r.error}</td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, tone = "neutral" }) {
  const toneClass = { good: "text-lime", bad: "text-danger", neutral: "text-text" }[tone];
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-fog mb-0.5">{label}</div>
      <div className={`font-display font-bold text-xl ${toneClass}`}>{value}</div>
    </div>
  );
}
