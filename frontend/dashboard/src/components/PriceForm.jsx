import { useState } from "react";
import { Card, Field, NumberInput, Button } from "./ui";
import ItemMarketFields from "./ItemMarketFields";
import { normalizeItem, normalizeMarket, num } from "../lib/normalize";
import { BUSINESS_GOALS, defaultItem, defaultMarket, defaultConstraints } from "../lib/defaults";

export default function PriceForm({ onSubmit, loading }) {
  const [item, setItem] = useState(defaultItem());
  const [market, setMarket] = useState(defaultMarket());
  const [goal, setGoal] = useState("maximize_profit");
  const [constraints, setConstraints] = useState(defaultConstraints());
  const [showAdvanced, setShowAdvanced] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit({
      business_goal: goal,
      item: normalizeItem(item, num),
      market_context: normalizeMarket(market, num),
      constraints: {
        min_margin_percent: num(constraints.min_margin_percent),
        max_price_increase_percent: num(constraints.max_price_increase_percent),
        max_price_decrease_percent: num(constraints.max_price_decrease_percent),
        price_ending: num(constraints.price_ending),
        min_confidence_for_apply: num(constraints.min_confidence_for_apply),
      },
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ItemMarketFields item={item} setItem={setItem} market={market} setMarket={setMarket} />

      <Card title="Бизнес-цель">
        <div className="grid grid-cols-1 gap-2">
          {BUSINESS_GOALS.map((g) => (
            <label
              key={g.value}
              className={`flex items-center justify-between px-3 py-2.5 rounded-lg border cursor-pointer transition-colors ${
                goal === g.value ? "border-lime/40 bg-lime/10" : "border-line bg-panel2 hover:border-line2"
              }`}
            >
              <div>
                <div className="text-sm font-medium text-text">{g.label}</div>
                <div className="text-[11px] text-muted">{g.hint}</div>
              </div>
              <input type="radio" name="goal" value={g.value} checked={goal === g.value} onChange={() => setGoal(g.value)} className="accent-accent" />
            </label>
          ))}
        </div>
      </Card>

      <Card>
        <button
          type="button"
          onClick={() => setShowAdvanced((v) => !v)}
          className="text-xs text-muted hover:text-text transition-colors mb-1"
        >
          {showAdvanced ? "− Скрыть ограничения" : "+ Ограничения (маржа, лимиты изменения цены)"}
        </button>
        {showAdvanced && (
          <div className="grid grid-cols-2 gap-x-3 mt-3">
            <Field label="Мин. маржа, %">
              <NumberInput value={constraints.min_margin_percent} onChange={(e) => setConstraints({ ...constraints, min_margin_percent: e.target.value })} />
            </Field>
            <Field label="Округление (.99 и т.п.)">
              <NumberInput step="0.01" min="0" max="0.99" value={constraints.price_ending} onChange={(e) => setConstraints({ ...constraints, price_ending: e.target.value })} />
            </Field>
            <Field label="Макс. рост цены, %">
              <NumberInput value={constraints.max_price_increase_percent} onChange={(e) => setConstraints({ ...constraints, max_price_increase_percent: e.target.value })} />
            </Field>
            <Field label="Макс. снижение цены, %">
              <NumberInput value={constraints.max_price_decrease_percent} onChange={(e) => setConstraints({ ...constraints, max_price_decrease_percent: e.target.value })} />
            </Field>
            <Field label="Мин. confidence для автоприменения">
              <NumberInput step="0.01" min="0" max="1" value={constraints.min_confidence_for_apply} onChange={(e) => setConstraints({ ...constraints, min_confidence_for_apply: e.target.value })} />
            </Field>
          </div>
        )}
      </Card>

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? "Считаем…" : "Рассчитать рекомендацию"}
      </Button>
    </form>
  );
}
