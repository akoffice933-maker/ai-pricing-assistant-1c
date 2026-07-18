export function Card({ title, subtitle, children, className = "", hover = false }) {
  return (
    <div className={`bg-panel border border-line rounded-2xl p-5 ${hover ? "card-hover" : ""} ${className}`}>
      {title && (
        <div className="mb-4">
          <h3 className="font-display font-bold text-text text-[15px] tracking-tight">{title}</h3>
          {subtitle && <p className="text-fog text-xs mt-0.5">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}

export function Field({ label, hint, children }) {
  return (
    <label className="block mb-3">
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-fog">{label}</span>
        {hint && <span className="text-[11px] text-fog/70">{hint}</span>}
      </div>
      {children}
    </label>
  );
}

const inputBase =
  "w-full bg-panel2 border border-line rounded-lg px-3 py-2 text-sm text-text placeholder:text-fog/50 " +
  "focus-ring outline-none transition-colors focus:border-lime/50";

export function TextInput(props) {
  return <input {...props} className={`${inputBase} ${props.className || ""}`} />;
}

export function NumberInput(props) {
  return <input type="number" {...props} className={`${inputBase} ${props.className || ""}`} />;
}

export function Select({ children, ...props }) {
  return (
    <select {...props} className={`${inputBase} ${props.className || ""}`}>
      {children}
    </select>
  );
}

export function Button({ variant = "primary", className = "", ...props }) {
  const base = "px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors focus-ring outline-none disabled:opacity-40 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-lime text-ink hover:bg-limedim",
    ghost: "bg-transparent text-mist hover:text-text border border-line hover:border-line2",
  };
  return <button {...props} className={`${base} ${variants[variant]} ${className}`} />;
}

export function Pill({ tone = "neutral", children }) {
  const tones = {
    neutral: "border-line bg-panel2 text-mist",
    good: "border-lime/40 bg-lime/10 text-lime",
    warn: "border-warn/40 bg-warn/10 text-warn",
    bad: "border-danger/40 bg-danger/10 text-danger",
    accent: "border-sky/40 bg-sky/10 text-sky",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.12em] font-medium px-2.5 py-1 rounded-md border ${tones[tone]}`}>
      {children}
    </span>
  );
}
