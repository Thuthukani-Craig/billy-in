"use client";

import { useEffect, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { StatCard } from "@/components/stat-card";
import { API_BASE_URL, AuthSession, ensureCsrfCookie, fetchJson } from "@/lib/api";

const recentInvoices = [
  { id: "INV-1001", customer: "Northwind Solutions", total: "R 18,450.00", status: "Paid" },
  { id: "INV-1004", customer: "Harbor Property Group", total: "R 7,200.00", status: "Partially paid" },
  { id: "INV-1009", customer: "Summit Logistics", total: "R 23,900.00", status: "Overdue" },
];

const recentQuotations = [
  { id: "QUO-0047", customer: "Crest Homes", total: "R 12,750.00", status: "Issued" },
  { id: "QUO-0012", customer: "Fieldstone Retail", total: "R 5,600.00", status: "Accepted" },
  { id: "QUO-0008", customer: "Mandla Build", total: "R 9,390.00", status: "Draft" },
];

const recentPayments = [
  { id: "PAY-1024", customer: "Northwind Solutions", amount: "R 18,450.00", method: "Bank transfer" },
  { id: "PAY-1025", customer: "Harbor Property Group", amount: "R 4,200.00", method: "Card" },
  { id: "PAY-1026", customer: "Khayelitsha Services", amount: "R 3,150.00", method: "Cash" },
];

export default function Home() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    const restoreSession = async () => {
      try {
        await ensureCsrfCookie();
        const currentUser = await fetchJson<AuthSession>("/api/v1/auth/me/");
        if (!active) return;
        setSession(currentUser);
      } catch {
        if (!active) return;
        setSession(null);
      }
    };

    void restoreSession();
    return () => {
      active = false;
    };
  }, []);

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await ensureCsrfCookie();
      const payload = await fetchJson<AuthSession>("/api/v1/auth/login/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: form.username,
          password: form.password,
        }),
      });

      setSession(payload);
      setForm({ username: "", password: "" });
    } catch (loginError) {
      const message = loginError instanceof Error ? loginError.message : "Unable to sign in.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const logout = () => {
    setSession(null);
    void fetchJson("/api/v1/auth/logout/", { method: "POST" }).catch(() => undefined);
  };

  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
        <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-lg shadow-slate-200/80">
          <div className="text-center">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600">Billy-in</div>
            <h1 className="mt-3 text-3xl font-semibold text-slate-900">Operations login</h1>
            <p className="mt-2 text-sm text-slate-500">Sign in to access the active tenant workspace.</p>
          </div>

          <form onSubmit={handleLogin} className="mt-8 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Username</label>
              <input
                value={form.username}
                onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                placeholder="admin"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                placeholder="••••••••"
              />
            </div>

            {error ? <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500">
            API endpoint: <span className="font-medium text-slate-700">{API_BASE_URL}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <LayoutShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Overview</p>
            <h2 className="mt-1 text-3xl font-semibold text-slate-900">Dashboard</h2>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700">
              {session.tenants[0]?.tenant__name ?? "Tenant workspace"}
            </div>
            <button onClick={logout} className="rounded-xl bg-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-300">
              Log out
            </button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Total invoiced" value="R 124,800.00" change="+12.5%" tone="blue" />
          <StatCard label="Payments received" value="R 87,240.00" change="+8.4%" tone="green" />
          <StatCard label="Outstanding" value="R 37,560.00" change="-3.2%" tone="amber" />
          <StatCard label="Overdue invoices" value="4" change="Needs follow-up" tone="slate" />
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Recent invoices</h3>
              <button className="text-sm font-medium text-blue-600">View all</button>
            </div>
            <div className="space-y-3">
              {recentInvoices.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <div>
                    <div className="font-medium text-slate-900">{invoice.id}</div>
                    <div className="text-sm text-slate-500">{invoice.customer}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-slate-900">{invoice.total}</div>
                    <div className="text-xs font-medium text-slate-500">{invoice.status}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <h3 className="text-lg font-semibold text-slate-900">Business summary</h3>
              <div className="mt-5 space-y-4">
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>Customers</span>
                  <span className="font-semibold text-slate-900">128</span>
                </div>
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>Active businesses</span>
                  <span className="font-semibold text-slate-900">3</span>
                </div>
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>Open quotations</span>
                  <span className="font-semibold text-slate-900">14</span>
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <h3 className="text-lg font-semibold text-slate-900">Recent payments</h3>
              <div className="mt-5 space-y-3">
                {recentPayments.map((payment) => (
                  <div key={payment.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <div>
                      <div className="font-medium text-slate-900">{payment.customer}</div>
                      <div className="text-xs text-slate-500">{payment.method}</div>
                    </div>
                    <div className="font-semibold text-emerald-700">{payment.amount}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
            <h3 className="text-lg font-semibold text-slate-900">Recent quotations</h3>
            <div className="mt-5 space-y-3">
              {recentQuotations.map((quote) => (
                <div key={quote.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <div>
                    <div className="font-medium text-slate-900">{quote.id}</div>
                    <div className="text-sm text-slate-500">{quote.customer}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-slate-900">{quote.total}</div>
                    <div className="text-xs font-medium text-slate-500">{quote.status}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
            <h3 className="text-lg font-semibold text-slate-900">Platform status</h3>
            <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-500">
              Signed in as <span className="font-semibold text-slate-700">{session.user.username}</span> and connected to the active tenant workflow.
            </div>
          </div>
        </div>
      </div>
    </LayoutShell>
  );
}
