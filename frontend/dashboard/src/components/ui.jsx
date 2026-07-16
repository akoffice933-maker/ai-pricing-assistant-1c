export function Card({ title, subtitle, children, className = "" }) {
  return (
    <div className={`bg-panel border border-line rounded-xl p-5 ${className}`}>
      {title && (
        <div className="mb-4">
          <h3 className="font-display font-bold text-text text-[15px] tracking-tight">{title}</h3>
          {subtitle && <p className="text-muted text-xs mt-0.5">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}

export function Field({ label, hint, children }) {
  return (
    <label className="block mb-3">
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-medium text-muted">{label}</span>
        {hint && <span className="text-[11px] text-muted/70">{hint}</span>}
      </div>
      {children}
    </label>
  );
}

const inputBase =
  "w-full bg-panel2 border border-line rounded-lg px-3 py-2 text-sm text-text placeholder:text-muted/50 " +
  "focus-ring outline-none transition-colors focus:border-accentSoft";

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
    primary: "bg-accent text-white hover:bg-accentSoft",
    ghost: "bg-transparent text-muted hover:text-text border border-line hover:border-muted",
  };
  return <button {...props} className={`${base} ${variants[variant]} ${className}`} />;
}

export function Pill({ tone = "neutral", children }) {
  const tones = {
    neutral: "bg-panel2 text-muted border-line",
    good: "bg-good/10 text-good border-good/30",
    warn: "bg-warn/10 text-warn border-warn/30",
    bad: "bg-bad/10 text-bad border-bad/30",
    accent: "bg-accentDim text-accentSoft border-accent/40",
  };
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-1 rounded-md border ${tones[tone]}`}>
      {children}
    </span>
  );
}
