import { Card, Field, TextInput, NumberInput, Select } from "./ui";
import { ITEM_TYPES } from "../lib/defaults";

export default function ItemMarketFields({ item, setItem, market, setMarket }) {
  const isService = item.item_type !== "product";

  return (
    <>
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
    </>
  );
}
