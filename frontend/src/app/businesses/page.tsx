"use client";

import { useEffect, useMemo, useState } from "react";

import { fetchJson } from "@/lib/api";
import { LayoutShell } from "@/components/layout-shell";

type Business = {
  id: number;
  tenant: number;
  name: string;
  trading_name: string;
  email: string;
  telephone: string;
  physical_address: string;
  primary_brand_colour: string;
  registration_number: string;
  vat_registration_number: string;
  is_active: boolean;
};

export default function BusinessesPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: "",
    trading_name: "",
    email: "",
    telephone: "",
    physical_address: "",
    primary_brand_colour: "#2563EB",
  });

  useEffect(() => {
    const loadBusinesses = async () => {
      try {
        const payload = await fetchJson<Business[]>("/api/v1/businesses/");
        setBusinesses(payload);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load businesses.");
      }
    };

    void loadBusinesses();
  }, []);

  const filteredBusinesses = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return businesses;
    return businesses.filter((business) => business.name.toLowerCase().includes(query));
  }, [businesses, search]);

  const addBusiness = async () => {
    const name = form.name.trim();
    if (!name) {
      setError("Business name is required.");
      return;
    }

    setError("");
    setMessage("");
    setIsSubmitting(true);

    try {
      const created = await fetchJson<Business>("/api/v1/businesses/", {
        method: "POST",
        body: JSON.stringify({
          name,
          trading_name: form.trading_name.trim() || name,
          email: form.email.trim(),
          telephone: form.telephone.trim(),
          physical_address: form.physical_address.trim(),
          primary_brand_colour: form.primary_brand_colour,
        }),
      });

      setBusinesses((current) => [created, ...current]);
      setForm({ name: "", trading_name: "", email: "", telephone: "", physical_address: "", primary_brand_colour: "#2563EB" });
      setMessage(`Business saved successfully: ${created.name}.`);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save business.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <LayoutShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Business management</p>
            <h2 className="mt-1 text-3xl font-semibold text-slate-900">Businesses</h2>
          </div>
          <div className="rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700">
            {businesses.length} record{businesses.length === 1 ? "" : "s"}
          </div>
        </div>

        {error ? <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
        {message ? <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div> : null}

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Business directory</h3>
              <div className="w-full max-w-xs">
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search business name"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none ring-0 transition focus:border-blue-500"
                />
              </div>
            </div>

            <div className="space-y-3">
              {filteredBusinesses.map((business) => (
                <div key={business.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl text-sm font-bold text-white" style={{ backgroundColor: business.primary_brand_colour || "#2563EB" }}>
                      {(business.name || "B").slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="text-base font-semibold text-slate-900">{business.name}</div>
                      <div className="text-sm text-slate-500">{business.trading_name || business.name}</div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 text-sm sm:items-end">
                    <div className="text-slate-600">{business.email || "No email"}</div>
                    <div className="flex items-center gap-2 text-slate-500">
                      <span>{business.telephone || "No phone"}</span>
                      <span className={business.is_active ? "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700" : "rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700"}>
                        {business.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
            <h3 className="text-lg font-semibold text-slate-900">Add business</h3>
            <div className="mt-5 space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-600">Business name</label>
                <input
                  value={form.name}
                  onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                  placeholder="Business name"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-600">Trading name</label>
                <input
                  value={form.trading_name}
                  onChange={(event) => setForm((current) => ({ ...current, trading_name: event.target.value }))}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                  placeholder="Trading name"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Email</label>
                  <input
                    value={form.email}
                    onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                    placeholder="mail@company.co.za"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Phone</label>
                  <input
                    value={form.telephone}
                    onChange={(event) => setForm((current) => ({ ...current, telephone: event.target.value }))}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                    placeholder="+27 00 000 0000"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-600">Physical address</label>
                <textarea
                  value={form.physical_address}
                  onChange={(event) => setForm((current) => ({ ...current, physical_address: event.target.value }))}
                  className="min-h-20 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                  placeholder="Business address"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-600">Primary brand colour</label>
                <input
                  type="color"
                  value={form.primary_brand_colour}
                  onChange={(event) => setForm((current) => ({ ...current, primary_brand_colour: event.target.value }))}
                  className="h-12 w-full rounded-xl border border-slate-200 bg-slate-50 p-1"
                />
              </div>
              <button
                type="button"
                onClick={addBusiness}
                disabled={isSubmitting}
                className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
              >
                {isSubmitting ? "Saving..." : "Save business"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </LayoutShell>
  );
}
