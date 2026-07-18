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
    <div className="bg-panel2 border border-line rounded-lg px-3 py-2 text-xs shadow-xl font-mono">
      <div className="text-text font-semibold">{p.price.toFixed(2)} за ед.</div>
      <div className="text-fog">спрос ≈ {p.expected_demand.toFixed(1)}</div>
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
          <CartesianGrid stroke="#1c2129" strokeDasharray="3 3" vertical={false} />
          {bounds && (
            <ReferenceArea
              x1={bounds.lower_bound}
              x2={bounds.upper_bound}
              fill="#d7ff3f"
              fillOpacity={0.07}
              stroke="none"
            />
          )}
          <XAxis
            dataKey="price"
            type="number"
            domain={["dataMin", "dataMax"]}
            tick={{ fill: "#5c6672", fontSize: 11 }}
            axisLine={{ stroke: "#1c2129" }}
            tickLine={false}
            tickFormatter={(v) => v.toFixed(0)}
          />
          <YAxis
            tick={{ fill: "#5c6672", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={36}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#5c6672", strokeDasharray: "3 3" }} />
          {currentPrice && (
            <ReferenceLine
              x={currentPrice}
              stroke="#5c6672"
              strokeDasharray="4 4"
              label={{ value: "текущая", position: "insideTopLeft", fill: "#5c6672", fontSize: 10 }}
            />
          )}
          <Line
            type="monotone"
            dataKey="expected_demand"
            stroke="#d7ff3f"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "#d7ff3f" }}
          />
          <ReferenceDot
            x={recPoint.price}
            y={recPoint.expected_demand}
            r={5}
            fill="#d7ff3f"
            stroke="#07080a"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
