import { useState } from "react";
import { Card, Field, TextInput, NumberInput, Select, Button } from "./ui";
import { BUSINESS_GOALS, ITEM_TYPES, defaultItem, defaultMarket, defaultConstraints } from "../lib/defaults";

function num(v) {
  return v === "" || v === null ? null : Number(v);
}

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
      item: {
        ...item,
        current_price: num(item.current_price),
        unit_cost: num(item.unit_cost),
        sales_last_30_days: num(item.sales_last_30_days),
        sales_last_90_days: num(item.sales_last_90_days),
        stock_quantity: item.item_type === "product" ? num(item.stock_quantity) : null,
        available_capacity: item.item_type !== "product" ? num(item.available_capacity) : null,
        target_margin_percent: num(item.target_margin_percent),
        quality_index: num(item.quality_index),
      },
      market_context: {
        ...market,
        market_price_median: num(market.market_price_median),
        market_demand_index: num(market.market_demand_index),
        promo_share: num(market.promo_share),
        availability_index: num(market.availability_index),
        seasonality_index: num(market.seasonality_index),
        data_freshness_days: num(market.data_freshness_days),
        coverage_score: num(market.coverage_score),
        confidence: num(market.confidence),
      },
      constraints: {
        min_margin_percent: num(constraints.min_margin_percent),
        max_price_increase_percent: num(constraints.max_price_increase_percent),
        max_price_decrease_percent: num(constraints.max_price_decrease_percent),
        price_ending: num(constraints.price_ending),
        min_confidence_for_apply: num(constraints.min_confidence_for_apply),
      },
    });
  }

  const isService = item.item_type !== "product";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Card title="Позиция" subtitle="Товар, услуга, проект или подписка">
        <div className="grid grid-cols-2 gap-x-3">
          <Field label="Название">
            <TextInput value={item.item_name} onChange={(e) => setItem({ ...item, item_name: e.target.value })} required />
          </Field>
          <Field label="Тип">
            <Select value={item.item_type} onChange={(e) => setItem({ ...item, item_type: e.target.value })}>
              {ITEM_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </Select>
          </Field>
          <Field label="Текущая цена">
            <NumberInput step="0.01" value={item.current_price} onChange={(e) => setItem({ ...item, current_price: e.target.value })} required />
          </Field>
          <Field label="Себестоимость">
            <NumberInput step="0.01" value={item.unit_cost} onChange={(e) => setItem({ ...item, unit_cost: e.target.value })} required />
          </Field>
          <Field label="Продажи за 30 дней">
            <NumberInput value={item.sales_last_30_days} onChange={(e) => setItem({ ...item, sales_last_30_days: e.target.value })} />
          </Field>
          <Field label="Продажи за 90 дней">
            <NumberInput value={item.sales_last_90_days} onChange={(e) => setItem({ ...item, sales_last_90_days: e.target.value })} />
          </Field>
          {isService ? (
            <Field label="Доступная мощность" hint="часы/слоты за период">
              <NumberInput value={item.available_capacity ?? ""} onChange={(e) => setItem({ ...item, available_capacity: e.target.value })} />
            </Field>
          ) : (
            <Field label="Остаток на складе">
              <NumberInput value={item.stock_quantity ?? ""} onChange={(e) => setItem({ ...item, stock_quantity: e.target.value })} />
            </Field>
          )}
          <Field label="Индекс качества/бренда" hint="1.0 = средний по рынку">
            <NumberInput step="0.01" value={item.quality_index} onChange={(e) => setItem({ ...item, quality_index: e.target.value })} />
          </Field>
        </div>
      </Card>

      <Card title="Рыночный контекст" subtitle="Из парсера конкурентов, CRM или ручного ввода">
        <div className="grid grid-cols-2 gap-x-3">
          <Field label="Медиана цены рынка">
            <NumberInput step="0.01" value={market.market_price_median} onChange={(e) => setMarket({ ...market, market_price_median: e.target.value })} required />
          </Field>
          <Field label="Индекс спроса рынка" hint="1.0 = норма">
            <NumberInput step="0.01" value={market.market_demand_index} onChange={(e) => setMarket({ ...market, market_demand_index: e.target.value })} />
          </Field>
          <Field label="Доля конкурентов в промо">
            <NumberInput step="0.01" min="0" max="1" value={market.promo_share} onChange={(e) => setMarket({ ...market, promo_share: e.target.value })} />
          </Field>
          <Field label="Индекс доступности у конкурентов">
            <NumberInput step="0.01" min="0" max="1" value={market.availability_index} onChange={(e) => setMarket({ ...market, availability_index: e.target.value })} />
          </Field>
          <Field label="Достоверность данных (confidence)">
            <NumberInput step="0.01" min="0" max="1" value={market.confidence} onChange={(e) => setMarket({ ...market, confidence: e.target.value })} />
          </Field>
          <Field label="Давность данных, дней">
            <NumberInput value={market.data_freshness_days} onChange={(e) => setMarket({ ...market, data_freshness_days: e.target.value })} />
          </Field>
        </div>
      </Card>

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
