type StatCardProps = {
  label: string;
  value: string;
  change?: string;
  tone?: "blue" | "green" | "amber" | "slate";
};

const toneStyles: Record<NonNullable<StatCardProps["tone"]>, string> = {
  blue: "bg-blue-50 text-blue-700",
  green: "bg-emerald-50 text-emerald-700",
  amber: "bg-amber-50 text-amber-700",
  slate: "bg-slate-100 text-slate-700",
};

export function StatCard({ label, value, change, tone = "slate" }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40">
      <div className="flex items-center justify-between gap-2">
        <div className="text-sm font-medium text-slate-500">{label}</div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${toneStyles[tone]}`}>
          {change ?? "Live"}
        </span>
      </div>
      <div className="mt-4 text-3xl font-semibold tracking-tight text-slate-900">{value}</div>
    </div>
  );
}
