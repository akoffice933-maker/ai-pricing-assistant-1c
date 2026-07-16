import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceDot,
  ReferenceArea,
  ReferenceLine,
} from "recharts";

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="bg-panel2 border border-line rounded-lg px-3 py-2 text-xs shadow-xl">
      <div className="text-text font-semibold">{p.price.toFixed(2)} за ед.</div>
      <div className="text-muted">спрос ≈ {p.expected_demand.toFixed(1)}</div>
    </div>
  );
}

export default function DemandCurveChart({ curve, recommendedPrice, currentPrice, bounds }) {
  if (!curve?.length) return null;
  const sorted = [...curve].sort((a, b) => a.price - b.price);
  const recPoint = sorted.reduce((closest, p) =>
    Math.abs(p.price - recommendedPrice) < Math.abs(closest.price - recommendedPrice) ? p : closest
  );

  return (
    <div className="h-64 -ml-2">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={sorted} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="#2C3438" strokeDasharray="3 3" vertical={false} />
          {bounds && (
            <ReferenceArea
              x1={bounds.lower_bound}
              x2={bounds.upper_bound}
              fill="#C0622A"
              fillOpacity={0.07}
              stroke="none"
            />
          )}
          <XAxis
            dataKey="price"
            type="number"
            domain={["dataMin", "dataMax"]}
            tick={{ fill: "#8B959B", fontSize: 11 }}
            axisLine={{ stroke: "#2C3438" }}
            tickLine={false}
            tickFormatter={(v) => v.toFixed(0)}
          />
          <YAxis
            tick={{ fill: "#8B959B", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#8B959B", strokeDasharray: "3 3" }} />
          {currentPrice && (
            <ReferenceLine
              x={currentPrice}
              stroke="#8B959B"
              strokeDasharray="4 4"
              label={{ value: "текущая", position: "insideTopLeft", fill: "#8B959B", fontSize: 10 }}
            />
          )}
          <Line
            type="monotone"
            dataKey="expected_demand"
            stroke="#E08A52"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "#E08A52" }}
          />
          <ReferenceDot
            x={recPoint.price}
            y={recPoint.expected_demand}
            r={5}
            fill="#C0622A"
            stroke="#14181B"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
