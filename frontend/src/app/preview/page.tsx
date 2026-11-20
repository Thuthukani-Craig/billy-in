import Link from "next/link";

import { LayoutShell } from "@/components/layout-shell";

const money = (value: number) =>
  new Intl.NumberFormat("en-ZA", { style: "currency", currency: "ZAR", maximumFractionDigits: 2 }).format(value);

const metrics = [
  { label: "Total invoiced", value: 82450, note: "Across issued invoices", accent: "bg-blue-500" },
  { label: "Payments received", value: 56200, note: "Recorded in this workspace", accent: "bg-emerald-500" },
  { label: "Outstanding", value: 26250, note: "Awaiting customer payment", accent: "bg-amber-500" },
  { label: "Active businesses", value: null, note: "Separate business workspaces", accent: "bg-violet-500" },
];

const activity = [
  { number: "INV-2026-0042", customer: "North Coast Projects", date: "20 Nov 2026", amount: 18500, status: "Awaiting payment" },
  { number: "INV-2026-0041", customer: "Mthembu Trading", date: "18 Nov 2026", amount: 12750, status: "Paid" },
  { number: "QUO-2026-0028", customer: "Coastal Facilities", date: "17 Nov 2026", amount: 24600, status: "Sent" },
];

export default function PreviewPage() {
  return (
    <LayoutShell>
      <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[11px] font-semibold text-blue-700">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
            INTERACTIVE UI PREVIEW · SAMPLE DATA
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-950 sm:text-[28px]">Good afternoon.</h2>
          <p className="mt-1.5 text-sm text-slate-500">A clearer picture of how your businesses are performing.</p>
        </div>
        <div className="flex gap-2">
          <Link href="/quotations" className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50">Explore quotations</Link>
          <span className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm">New document</span>
        </div>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <article key={metric.label} className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_12px_rgba(15,23,42,0.025)]">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-slate-500">{metric.label}</p>
              <span className={`h-2 w-2 rounded-full ${metric.accent}`} />
            </div>
            <p className="mt-4 text-2xl font-semibold tracking-tight text-slate-950">{metric.value === null ? "03" : money(metric.value)}</p>
            <p className="mt-2 text-xs text-slate-400">{metric.note}</p>
          </article>
        ))}
      </section>

      <div className="mt-7 grid gap-5 xl:grid-cols-[1.5fr_1fr]">
        <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_2px_12px_rgba(15,23,42,0.025)]">
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <div><h3 className="text-sm font-semibold text-slate-900">Recent activity</h3><p className="mt-1 text-xs text-slate-400">Your latest financial documents</p></div>
            <span className="rounded-lg bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-500">View all</span>
          </div>
          <div className="divide-y divide-slate-100">
            {activity.map((item) => (
              <div key={item.number} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-800">{item.number}</p><p className="mt-1 text-xs text-slate-400">{item.customer} · {item.date}</p></div>
                <div className="flex items-center justify-between gap-4 sm:justify-end"><span className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${item.status === "Paid" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{item.status}</span><span className="text-sm font-semibold text-slate-800">{money(item.amount)}</span></div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_12px_rgba(15,23,42,0.025)]">
          <div className="flex items-center justify-between"><h3 className="text-sm font-semibold text-slate-900">Workspace snapshot</h3><span className="text-xs text-slate-400">Illustrative</span></div>
          <div className="mt-5 space-y-5">
            {[{ name: "Vala Technologies", share: "58%", amount: "R 47,800", width: "58%" }, { name: "MEGG Maintenance", share: "31%", amount: "R 25,650", width: "31%" }, { name: "Qondisa", share: "11%", amount: "R 9,000", width: "11%" }].map((business) => (
              <div key={business.name}>
                <div className="mb-2 flex items-center justify-between gap-3"><span className="text-xs font-medium text-slate-700">{business.name}</span><span className="text-xs text-slate-500">{business.amount}</span></div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-blue-500" style={{ width: business.width }} /></div>
              </div>
            ))}
          </div>
          <div className="mt-7 rounded-xl bg-slate-50 p-4"><p className="text-xs font-semibold text-slate-700">Designed for multiple businesses</p><p className="mt-1.5 text-xs leading-5 text-slate-500">Keep each business's customers, documents and financial activity organised while viewing the wider portfolio.</p></div>
        </section>
      </div>

      <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800">
        This is a visual preview only. Figures and activity are sample data; authentication, saving and live financial records are not connected on this public preview.
      </div>
    </LayoutShell>
  );
}
