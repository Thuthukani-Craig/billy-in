"use client";

import { useEffect, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { API_BASE_URL, AuthSession, ensureCsrfCookie, fetchJson } from "@/lib/api";

type DashboardSummary = {
  business_count: number;
  active_business_count: number;
  customer_count: number;
  total_invoiced: number | string;
  total_payments_received: number | string;
  outstanding_balances: number | string;
  overdue_invoices: number;
  recent_invoices: Array<{ id: number; document_number: string; customer_name: string; total: number; status: string; created_at: string }>;
  recent_quotations: Array<{ id: number; document_number: string; customer_name: string; total: number; status: string; created_at: string }>;
  recent_payments: Array<{ id: number; customer_name: string; amount: number; payment_method: string; payment_date: string }>;
};

const money = (value: number | string) =>
  new Intl.NumberFormat("en-ZA", { style: "currency", currency: "ZAR", maximumFractionDigits: 2 }).format(Number(value || 0));

const dateLabel = (value: string) =>
  new Intl.DateTimeFormat("en-ZA", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));

function MetricCard({ label, value, caption, accent }: { label: string; value: string; caption: string; accent: string }) {
  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_2px_12px_rgba(15,23,42,0.025)]">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <span className={`h-2 w-2 rounded-full ${accent}`} />
      </div>
      <p className="mt-4 text-2xl font-semibold tracking-tight text-slate-950 sm:text-[1.8rem]">{value}</p>
      <p className="mt-2 text-xs text-slate-400">{caption}</p>
    </section>
  );
}

function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase().replaceAll("_", " ");
  const styles = normalized.includes("paid")
    ? "bg-emerald-50 text-emerald-700"
    : normalized.includes("overdue") || normalized.includes("reject")
      ? "bg-rose-50 text-rose-700"
      : normalized.includes("draft")
        ? "bg-slate-100 text-slate-600"
        : "bg-blue-50 text-blue-700";
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ${styles}`}>{normalized}</span>;
}

export default function Home() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [summaryError, setSummaryError] = useState("");
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);

  useEffect(() => {
    let active = true;
    const restoreSession = async () => {
      try {
        await ensureCsrfCookie();
        const currentUser = await fetchJson<AuthSession>("/api/v1/auth/me/");
        if (active) setSession(currentUser);
      } catch {
        if (active) setSession(null);
      }
    };
    void restoreSession();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!session) return;
    let active = true;
    setIsLoadingSummary(true);
    setSummaryError("");
    fetchJson<DashboardSummary>("/api/v1/reporting/dashboard/")
      .then((payload) => { if (active) setSummary(payload); })
      .catch((loadError) => {
        if (active) setSummaryError(loadError instanceof Error ? loadError.message : "Unable to load financial overview.");
      })
      .finally(() => { if (active) setIsLoadingSummary(false); });
    return () => { active = false; };
  }, [session]);

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      await ensureCsrfCookie();
      const payload = await fetchJson<AuthSession>("/api/v1/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setSession(payload);
      setForm({ username: "", password: "" });
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const logout = () => {
    setSession(null);
    setSummary(null);
    void fetchJson("/api/v1/auth/logout/", { method: "POST" }).catch(() => undefined);
  };

  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f4f6fa] px-4">
        <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/60">
          <div className="mb-8">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-lg font-semibold text-white">b.</div>
            <p className="mt-6 text-xs font-semibold uppercase tracking-[0.2em] text-blue-600">Billy-in workspace</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Welcome back.</h1>
            <p className="mt-2 text-sm leading-6 text-slate-500">Sign in to manage your businesses and financial operations.</p>
          </div>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Username</label>
              <input required autoComplete="username" value={form.username} onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-sm outline-none transition focus:border-blue-500 focus:bg-white" placeholder="Your username" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Password</label>
              <input required type="password" autoComplete="current-password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-3 text-sm outline-none transition focus:border-blue-500 focus:bg-white" placeholder="Your password" />
            </div>
            {error ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-700">{error}</div> : null}
            <button type="submit" disabled={isSubmitting} className="w-full rounded-xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? "Signing in…" : "Sign in to Billy-in"}</button>
          </form>
          <p className="mt-6 text-center text-xs text-slate-400">Secure business workspace · {API_BASE_URL}</p>
        </div>
      </div>
    );
  }

  return (
    <LayoutShell>
      <div className="space-y-7">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">Business overview</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Good to see you, {session.user.username}.</h2>
            <p className="mt-2 text-sm text-slate-500">Here’s what’s happening across your workspace.</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">Workspace active</span>
            <button onClick={logout} className="rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-950">Log out</button>
          </div>
        </div>

        {summaryError ? <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">The financial overview could not be loaded: {summaryError}</div> : null}

        <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
          <MetricCard label="Total invoiced" value={isLoadingSummary && !summary ? "—" : money(summary?.total_invoiced ?? 0)} caption="Value of recorded invoices" accent="bg-blue-500" />
          <MetricCard label="Payments received" value={isLoadingSummary && !summary ? "—" : money(summary?.total_payments_received ?? 0)} caption="Payments recorded in the system" accent="bg-emerald-500" />
          <MetricCard label="Outstanding balance" value={isLoadingSummary && !summary ? "—" : money(summary?.outstanding_balances ?? 0)} caption="Remaining invoice balances" accent="bg-amber-500" />
          <MetricCard label="Overdue invoices" value={isLoadingSummary && !summary ? "—" : String(summary?.overdue_invoices ?? 0)} caption="Invoices needing attention" accent="bg-rose-500" />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <section className="rounded-2xl border border-slate-200/80 bg-white px-5 py-4">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Businesses</p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">{summary?.active_business_count ?? "—"}</p>
            <p className="mt-1 text-xs text-slate-500">of {summary?.business_count ?? "—"} registered</p>
          </section>
          <section className="rounded-2xl border border-slate-200/80 bg-white px-5 py-4">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Customers</p>
            <p className="mt-2 text-2xl font-semibold text-slate-950">{summary?.customer_count ?? "—"}</p>
            <p className="mt-1 text-xs text-slate-500">Across your workspace</p>
          </section>
          <section className="rounded-2xl border border-slate-200/80 bg-white px-5 py-4">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Workspace access</p>
            <p className="mt-2 text-2xl font-semibold capitalize text-slate-950">{session.tenants.length} tenant{session.tenants.length === 1 ? "" : "s"}</p>
            <p className="mt-1 text-xs text-slate-500">Authenticated memberships</p>
          </section>
        </div>

        <div className="grid gap-5 2xl:grid-cols-[1.2fr_0.8fr]">
          <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white">
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
              <div><h3 className="font-semibold text-slate-950">Recent invoices</h3><p className="mt-1 text-xs text-slate-400">Latest invoice activity</p></div>
              <a href="/invoices" className="text-sm font-medium text-blue-600 hover:text-blue-700">View invoices →</a>
            </div>
            {summary?.recent_invoices.length ? (
              <div className="divide-y divide-slate-100">
                {summary.recent_invoices.map((invoice) => (
                  <div key={invoice.id} className="flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div><p className="text-sm font-semibold text-slate-800">{invoice.document_number}</p><p className="mt-1 text-sm text-slate-500">{invoice.customer_name} · {dateLabel(invoice.created_at)}</p></div>
                    <div className="flex items-center justify-between gap-4 sm:justify-end"><span className="text-sm font-semibold text-slate-900">{money(invoice.total)}</span><StatusPill status={invoice.status} /></div>
                  </div>
                ))}
              </div>
            ) : <div className="px-5 py-10 text-center text-sm text-slate-400">{isLoadingSummary ? "Loading invoice activity…" : "No invoices have been recorded yet."}</div>}
          </section>

          <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white">
            <div className="border-b border-slate-100 px-5 py-4"><h3 className="font-semibold text-slate-950">Recent payments</h3><p className="mt-1 text-xs text-slate-400">Money recorded as received</p></div>
            {summary?.recent_payments.length ? (
              <div className="divide-y divide-slate-100">
                {summary.recent_payments.map((payment) => (
                  <div key={payment.id} className="flex items-center justify-between gap-3 px-5 py-4">
                    <div><p className="text-sm font-medium text-slate-800">{payment.customer_name}</p><p className="mt-1 text-xs capitalize text-slate-400">{payment.payment_method.replaceAll("_", " ")} · {dateLabel(payment.payment_date)}</p></div>
                    <p className="whitespace-nowrap text-sm font-semibold text-emerald-700">+{money(payment.amount)}</p>
                  </div>
                ))}
              </div>
            ) : <div className="px-5 py-10 text-center text-sm text-slate-400">{isLoadingSummary ? "Loading payment activity…" : "No payments have been recorded yet."}</div>}
          </section>
        </div>

        <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white">
          <div className="border-b border-slate-100 px-5 py-4"><h3 className="font-semibold text-slate-950">Recent quotations</h3><p className="mt-1 text-xs text-slate-400">Your latest customer proposals</p></div>
          {summary?.recent_quotations.length ? (
            <div className="divide-y divide-slate-100">
              {summary.recent_quotations.map((quote) => (
                <div key={quote.id} className="flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <div><p className="text-sm font-semibold text-slate-800">{quote.document_number}</p><p className="mt-1 text-sm text-slate-500">{quote.customer_name} · {dateLabel(quote.created_at)}</p></div>
                  <div className="flex items-center justify-between gap-4 sm:justify-end"><span className="text-sm font-semibold text-slate-900">{money(quote.total)}</span><StatusPill status={quote.status} /></div>
                </div>
              ))}
            </div>
          ) : <div className="px-5 py-10 text-center text-sm text-slate-400">{isLoadingSummary ? "Loading quotations…" : "No quotations have been created yet."}</div>}
        </section>
        <p className="text-xs leading-5 text-slate-400">Figures reflect records currently stored in Billy-in. Accounting statements and cash-flow analysis will be introduced after the financial ledger is implemented.</p>
      </div>
    </LayoutShell>
  );
}
