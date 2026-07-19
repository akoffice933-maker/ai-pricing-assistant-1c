import { useMemo, useState } from "react";
import { Card, Field, NumberInput } from "./ui";

function fmtMoney(n) {
  if (!isFinite(n)) return "—";
  return n.toLocaleString("ru-RU", { maximumFractionDigits: 0 });
}

function fmtMonths(n) {
  if (!isFinite(n) || n <= 0) return "—";
  if (n > 60) return "> 60 мес.";
  return `${n.toFixed(1)} мес.`;
}

const DEFAULTS = {
  positions: 500,
  avgMonthlyRevenuePerPosition: 45000,
  marginPercent: 25,
  upliftPercent: 4,
  manualAnalysisCostMonthly: 80000,
  projectCost: 1154000,
};

export default function RoiCalculatorPage() {
  const [inputs, setInputs] = useState(DEFAULTS);

  function set(key) {
    return (e) => setInputs({ ...inputs, [key]: e.target.value === "" ? "" : Number(e.target.value) });
  }

  const calc = useMemo(() => {
    const n = (v) => (typeof v === "number" && isFinite(v) ? v : 0);
    const totalMonthlyRevenue = n(inputs.positions) * n(inputs.avgMonthlyRevenuePerPosition);
    const totalMonthlyProfit = totalMonthlyRevenue * (n(inputs.marginPercent) / 100);
    const additionalMonthlyProfit = totalMonthlyProfit * (n(inputs.upliftPercent) / 100);
    const monthlySavings = n(inputs.manualAnalysisCostMonthly);
    const totalMonthlyValue = additionalMonthlyProfit + monthlySavings;
    const annualValue = totalMonthlyValue * 12;
    const paybackMonths = totalMonthlyValue > 0 ? n(inputs.projectCost) / totalMonthlyValue : Infinity;
    return { totalMonthlyRevenue, totalMonthlyProfit, additionalMonthlyProfit, monthlySavings, totalMonthlyValue, annualValue, paybackMonths };
  }, [inputs]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-6 items-start">
      <div className="space-y-4">
        <Card title="Портфель позиций">
          <Field label="Количество позиций (SKU) под управлением">
            <NumberInput value={inputs.positions} onChange={set("positions")} />
          </Field>
          <Field label="Средняя выручка на позицию в месяц">
            <NumberInput value={inputs.avgMonthlyRevenuePerPosition} onChange={set("avgMonthlyRevenuePerPosition")} />
          </Field>
          <Field label="Средняя маржа, %">
            <NumberInput value={inputs.marginPercent} onChange={set("marginPercent")} />
          </Field>
        </Card>

        <Card title="Эффект от ценообразования" subtitle="Ваша оценка/отраслевой бенчмарк — не гарантия">
          <Field label="Ожидаемый uplift прибыли, %" hint="обычно 2-8% для pricing-оптимизации">
            <NumberInput value={inputs.upliftPercent} onChange={set("upliftPercent")} />
          </Field>
          <Field label="Экономия на ручном анализе, ₽/мес" hint="время сотрудников, которое сейчас уходит на это вручную">
            <NumberInput value={inputs.manualAnalysisCostMonthly} onChange={set("manualAnalysisCostMonthly")} />
          </Field>
        </Card>

        <Card title="Стоимость проекта">
          <Field label="Стоимость внедрения, ₽" hint="см. коммерческое предложение">
            <NumberInput value={inputs.projectCost} onChange={set("projectCost")} />
          </Field>
        </Card>
      </div>

      <div className="space-y-4">
        <Card>
          <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-fog mb-1">Срок окупаемости</div>
          <div className="font-display font-extrabold text-4xl text-text tracking-tight">
            {fmtMonths(calc.paybackMonths)}
          </div>
        </Card>

        <Card title="Экономический эффект">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Доп. прибыль от uplift, ₽/мес" value={fmtMoney(calc.additionalMonthlyProfit)} />
            <Stat label="Экономия на анализе, ₽/мес" value={fmtMoney(calc.monthlySavings)} />
            <Stat label="Итого эффект, ₽/мес" value={fmtMoney(calc.totalMonthlyValue)} highlight />
            <Stat label="Итого эффект, ₽/год" value={fmtMoney(calc.annualValue)} highlight />
          </div>
        </Card>

        <Card title="Контекст портфеля">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Выручка портфеля, ₽/мес" value={fmtMoney(calc.totalMonthlyRevenue)} />
            <Stat label="Валовая прибыль, ₽/мес" value={fmtMoney(calc.totalMonthlyProfit)} />
          </div>
        </Card>

        <Card>
          <p className="text-[11px] text-fog leading-relaxed">
            Это калькулятор для оценки порядка величины, не финансовый прогноз. Uplift % —
            параметр, который вы задаёте сами (отраслевой бенчмарк или пилотные данные), а не
            то, что гарантированно даёт эта система — см.{" "}
            <a
              href="https://github.com/akoffice933-maker/ai-pricing-assistant-1c#ограничения-модели--честно"
              target="_blank"
              rel="noreferrer"
              className="text-lime hover:text-limedim"
            >
              «Ограничения модели»
            </a>{" "}
            в README: эластичность сейчас — калиброванная эвристика, не обученная и не
            провалидированная модель.
          </p>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value, highlight = false }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-fog mb-0.5">{label}</div>
      <div className={`text-sm font-semibold ${highlight ? "text-lime" : "text-text"}`}>{value}</div>
    </div>
  );
}
