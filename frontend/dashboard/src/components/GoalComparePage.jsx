import { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import { Card, Button, Pill } from "./ui";
import ItemMarketFields from "./ItemMarketFields";
import { normalizeItem, normalizeMarket, num } from "../lib/normalize";
import { BUSINESS_GOALS, defaultItem, defaultMarket } from "../lib/defaults";
import { api, ApiError } from "../api";

function fmt(n, digits = 0) {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("ru-RU", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

const BAR_COLOR = "#d7ff3f";

export default function GoalComparePage() {
  const [item, setItem] = useState(defaultItem());
  const [market, setMarket] = useState(defaultMarket());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rows, setRows] = useState(null);

  async function handleCompare(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setRows(null);
    try {
      const payloadBase = {
        item: normalizeItem(item, num),
        market_context: normalizeMarket(market, num),
      };
      const settled = await Promise.all(
        BUSINESS_GOALS.map((g) =>
          api
            .recommendPrice({ ...payloadBase, business_goal: g.value })
            .then((result) => ({ goal: g, result, error: null }))
            .catch((err) => ({ goal: g, result: null, error: err instanceof ApiError ? err.message : String(err) }))
        )
      );
      setRows(settled);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Непредвиденная ошибка.");
    } finally {
      setLoading(false);
    }
  }

  const chartData =
    rows?.filter((r) => r.result).map((r) => ({
      name: r.goal.label,
      price: r.result.recommended_price,
    })) ?? [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-6 items-start">
      <form onSubmit={handleCompare} className="space-y-4">
        <ItemMarketFields item={item} setItem={setItem} market={market} setMarket={setMarket} />
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Считаем 6 целей…" : "Сравнить все бизнес-цели"}
        </Button>
      </form>

      <div className="space-y-4">
        {!rows && !loading && !error && (
          <Card>
            <div className="text-fog text-sm py-12 text-center">
              Заполните позицию и рыночный контекст слева — рассчитаем рекомендованную цену
              сразу по всем 6 бизнес-целям для сравнения.
            </div>
          </Card>
        )}

        {error && (
          <Card title="Ошибка">
            <p className="text-danger text-sm">{error}</p>
          </Card>
        )}

        {rows && (
          <>
            <Card title="Цена по целям" subtitle="Одна и та же позиция, один и тот же рынок">
              <div className="h-56 -ml-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
                    <CartesianGrid stroke="#1c2129" strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="name"
                      tick={{ fill: "#5c6672", fontSize: 10 }}
                      axisLine={{ stroke: "#1c2129" }}
                      tickLine={false}
                      interval={0}
                      angle={-20}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fill: "#5c6672", fontSize: 11 }} axisLine={false} tickLine={false} width={44} />
                    <Tooltip
                      cursor={{ fill: "rgba(215,255,63,0.06)" }}
                      contentStyle={{ background: "#101318", border: "1px solid #1c2129", borderRadius: 8, fontFamily: "JetBrains Mono" }}
                      labelStyle={{ color: "#e8ecf1" }}
                    />
                    <Bar dataKey="price" radius={[4, 4, 0, 0]}>
                      {chartData.map((_, i) => (
                        <Cell key={i} fill={BAR_COLOR} fillOpacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title="Таблица сравнения" className="!p-0 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="font-mono text-[10px] uppercase tracking-[0.1em] text-fog border-b border-line">
                    <th className="text-left px-4 py-2.5">Цель</th>
                    <th className="text-right px-4 py-2.5">Цена</th>
                    <th className="text-right px-4 py-2.5">Спрос</th>
                    <th className="text-right px-4 py-2.5">Выручка</th>
                    <th className="text-right px-4 py-2.5">Прибыль</th>
                    <th className="text-right px-4 py-2.5">Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.goal.value} className="border-b border-line/50 last:border-0">
                      <td className="px-4 py-2.5 text-text">{r.goal.label}</td>
                      {r.result ? (
                        <>
                          <td className="px-4 py-2.5 text-right font-display font-semibold text-text">
                            {fmt(r.result.recommended_price, 2)}
                          </td>
                          <td className="px-4 py-2.5 text-right text-mist">{fmt(r.result.expected_demand, 1)}</td>
                          <td className="px-4 py-2.5 text-right text-mist">{fmt(r.result.expected_revenue, 0)}</td>
                          <td className="px-4 py-2.5 text-right text-mist">{fmt(r.result.expected_gross_profit, 0)}</td>
                          <td className="px-4 py-2.5 text-right">
                            <Pill tone={r.result.is_reliable ? "good" : "warn"}>
                              {r.result.is_reliable ? "OK" : "Ручной review"}
                            </Pill>
                          </td>
                        </>
                      ) : (
                        <td className="px-4 py-2.5 text-danger text-xs" colSpan={5}>{r.error}</td>
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
