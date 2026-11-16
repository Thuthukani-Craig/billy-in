"use client";

import { useEffect, useMemo, useState } from "react";

import { fetchJson } from "@/lib/api";
import { LayoutShell } from "@/components/layout-shell";

type Business = {
  id: number;
  name: string;
  trading_name: string;
};

type Customer = {
  id: number;
  business: number;
  business_name: string;
  customer_type: "COMPANY" | "INDIVIDUAL";
  name: string;
  contact_person: string;
  email: string;
  telephone: string;
  physical_address: string;
  vat_number: string;
  is_active: boolean;
};

export default function CustomersPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [selectedBusinessId, setSelectedBusinessId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({
    business: "",
    customer_type: "COMPANY" as Customer["customer_type"],
    name: "",
    contact_person: "",
    email: "",
    telephone: "",
    physical_address: "",
  });

  useEffect(() => {
    const loadBusinesses = async () => {
      try {
        const payload = await fetchJson<Business[]>("/api/v1/businesses/");
        setBusinesses(payload);
        if (payload.length > 0) {
          const firstId = String(payload[0].id);
          setSelectedBusinessId(firstId);
          setForm((current) => ({ ...current, business: firstId }));
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load businesses.");
      }
    };

    void loadBusinesses();
  }, []);

  useEffect(() => {
    if (!selectedBusinessId) return;

    const loadCustomers = async () => {
      try {
        const payload = await fetchJson<Customer[]>(`/api/v1/customers/?business_id=${selectedBusinessId}`);
        setCustomers(payload);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load customers.");
      }
    };

    void loadCustomers();
  }, [selectedBusinessId]);

  const filteredCustomers = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return customers;
    return customers.filter((customer) => customer.name.toLowerCase().includes(query));
  }, [customers, search]);

  const addCustomer = async () => {
    if (!selectedBusinessId) {
      setError("Select a valid business before creating a customer.");
      return;
    }

    const name = form.name.trim();
    if (!name) {
      setError("Customer name is required.");
      return;
    }

    setError("");
    setMessage("");
    setIsSubmitting(true);

    try {
      const created = await fetchJson<Customer>("/api/v1/customers/", {
        method: "POST",
        body: JSON.stringify({
          business: Number(selectedBusinessId),
          customer_type: form.customer_type,
          name,
          contact_person: form.contact_person.trim(),
          email: form.email.trim(),
          telephone: form.telephone.trim(),
          physical_address: form.physical_address.trim(),
        }),
      });

      setCustomers((current) => [created, ...current]);
      setSelectedBusinessId(String(created.business));
      setForm({
        business: String(created.business),
        customer_type: "COMPANY",
        name: "",
        contact_person: "",
        email: "",
        telephone: "",
        physical_address: "",
      });
      setMessage(`Customer saved successfully: ${created.name}.`);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save customer.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <LayoutShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Customer management</p>
            <h2 className="mt-1 text-3xl font-semibold text-slate-900">Customers</h2>
          </div>
          <div className="rounded-full bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700">
            {customers.length} record{customers.length === 1 ? "" : "s"}
          </div>
        </div>

        {error ? <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
        {message ? <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div> : null}

        <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Customer directory</h3>
              <div className="w-full max-w-xs">
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search customer"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
                />
              </div>
            </div>

            <div className="space-y-3">
              {filteredCustomers.map((customer) => (
                <div key={customer.id} className="flex flex-col gap-3 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="text-base font-semibold text-slate-900">{customer.name}</div>
                    <div className="mt-1 text-sm text-slate-500">{customer.business_name} • {customer.customer_type === "COMPANY" ? "Company" : "Individual"}</div>
                  </div>

                  <div className="flex flex-col gap-2 text-sm text-slate-600 sm:items-end">
                    <div>{customer.email || "No email"}</div>
                    <div className="flex items-center gap-2">
                      <span>{customer.telephone || "No phone"}</span>
                      <span className={customer.is_active ? "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700" : "rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700"}>
                        {customer.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
            <h3 className="text-lg font-semibold text-slate-900">Add customer</h3>
            <div className="mt-5 space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-600">Business</label>
                <select
                  value={selectedBusinessId}
                  onChange={(event) => {
                    setSelectedBusinessId(event.target.value);
                    setForm((current) => ({ ...current, business: event.target.value }));
                  }}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                >
                  {businesses.map((business) => (
                    <option key={business.id} value={String(business.id)}>{business.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Type</label>
                  <select
                    value={form.customer_type}
                    onChange={(event) => setForm((current) => ({ ...current, customer_type: event.target.value as Customer["customer_type"] }))}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                  >
                    <option value="COMPANY">Company</option>
                    <option value="INDIVIDUAL">Individual</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Customer name</label>
                  <input
                    value={form.name}
                    onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                    placeholder="Customer name"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-600">Contact person</label>
                <input
                  value={form.contact_person}
                  onChange={(event) => setForm((current) => ({ ...current, contact_person: event.target.value }))}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                  placeholder="Primary contact"
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Email</label>
                  <input
                    value={form.email}
                    onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                    placeholder="customer@example.com"
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
                <label className="mb-1.5 block text-sm font-medium text-slate-600">Address</label>
                <textarea
                  value={form.physical_address}
                  onChange={(event) => setForm((current) => ({ ...current, physical_address: event.target.value }))}
                  className="min-h-20 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                  placeholder="Customer address"
                />
              </div>
              <button
                type="button"
                onClick={addCustomer}
                disabled={isSubmitting}
                className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
              >
                {isSubmitting ? "Saving..." : "Save customer"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </LayoutShell>
  );
}
