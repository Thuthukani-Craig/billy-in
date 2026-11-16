"use client";

import { useEffect, useMemo, useState } from "react";

import { LayoutShell } from "@/components/layout-shell";
import { fetchJson } from "@/lib/api";

type Business = {
  id: number;
  name: string;
  trading_name: string;
  email: string;
  telephone: string;
  physical_address: string;
  primary_brand_colour: string;
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
};

type LineItem = {
  description: string;
  quantity: string;
  unit_of_measure: string;
  unit_price: string;
  tax_rate: string;
  discount: string;
};

type DocumentResponse = {
  id: number;
  document_number: string;
  document_type: string;
  status: string;
  total: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  business_name: string;
  customer_name: string;
  issue_date: string;
  due_date: string | null;
  notes: string;
};

type HistoryDocument = DocumentResponse & { created_at: string };

const emptyLineItem = (): LineItem => ({
  description: "",
  quantity: "1",
  unit_of_measure: "hour",
  unit_price: "0",
  tax_rate: "15",
  discount: "0",
});

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("en-ZA", {
    style: "currency",
    currency: "ZAR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);

export default function QuotationsPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [documents, setDocuments] = useState<HistoryDocument[]>([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>("");
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>("");
  const [notes, setNotes] = useState("");
  const [issueDate, setIssueDate] = useState(() =>
    typeof window === "undefined" ? "" : new Date().toISOString().slice(0, 10),
  );
  const [dueDate, setDueDate] = useState("");
  const [lineItems, setLineItems] = useState<LineItem[]>([emptyLineItem()]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdDocument, setCreatedDocument] = useState<DocumentResponse | null>(null);
  const [customerForm, setCustomerForm] = useState({
    name: "",
    contact_person: "",
    email: "",
    telephone: "",
    physical_address: "",
    customer_type: "COMPANY" as Customer["customer_type"],
  });

  const selectedBusiness = businesses.find((business) => String(business.id) === selectedBusinessId) ?? null;

  useEffect(() => {
    const loadBusinesses = async () => {
      try {
        const payload = await fetchJson<Business[]>("/api/v1/businesses/");
        setBusinesses(payload);
        if (payload.length > 0) {
          const firstBusinessId = String(payload[0].id);
          setSelectedBusinessId(firstBusinessId);
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
        const response = await fetchJson<Customer[]>(`/api/v1/customers/?business_id=${selectedBusinessId}`);
        setCustomers(response);
        if (response.length > 0) {
          setSelectedCustomerId(String(response[0].id));
        } else {
          setSelectedCustomerId("");
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load customers.");
      }
    };

    const loadDocuments = async () => {
      try {
        const response = await fetchJson<HistoryDocument[]>(`/api/v1/documents/?business_id=${selectedBusinessId}`);
        setDocuments(response);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to load documents.");
      }
    };

    void loadCustomers();
    void loadDocuments();
  }, [selectedBusinessId]);

  const subtotal = useMemo(
    () => lineItems.reduce((sum, item) => sum + Number(item.quantity || 0) * Number(item.unit_price || 0), 0),
    [lineItems],
  );

  const discountTotal = useMemo(
    () => lineItems.reduce((sum, item) => sum + Number(item.discount || 0), 0),
    [lineItems],
  );

  const taxTotal = useMemo(
    () =>
      lineItems.reduce((sum, item) => {
        const quantity = Number(item.quantity || 0);
        const unitPrice = Number(item.unit_price || 0);
        const discount = Number(item.discount || 0);
        const taxable = quantity * unitPrice - discount;
        const taxRate = Number(item.tax_rate || 0) / 100;
        return sum + taxable * taxRate;
      }, 0),
    [lineItems],
  );

  const grandTotal = subtotal - discountTotal + taxTotal;

  const updateLineItem = (index: number, field: keyof LineItem, value: string) => {
    setLineItems((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item)));
  };

  const addLineItem = () => setLineItems((current) => [...current, emptyLineItem()]);
  const removeLineItem = (index: number) => {
    setLineItems((current) => (current.length > 1 ? current.filter((_, itemIndex) => itemIndex !== index) : current));
  };

  const createCustomer = async () => {
    if (!selectedBusinessId) {
      setError("Choose a business before creating a customer.");
      return;
    }

    const customerName = customerForm.name.trim();
    if (!customerName) {
      setError("Customer name is required.");
      return;
    }

    try {
      const created = await fetchJson<Customer>("/api/v1/customers/", {
        method: "POST",
        body: JSON.stringify({
          business: Number(selectedBusinessId),
          customer_type: customerForm.customer_type,
          name: customerName,
          contact_person: customerForm.contact_person.trim(),
          email: customerForm.email.trim(),
          telephone: customerForm.telephone.trim(),
          physical_address: customerForm.physical_address.trim(),
        }),
      });

      setCustomers((current) => [created, ...current]);
      setSelectedCustomerId(String(created.id));
      setCustomerForm({
        name: "",
        contact_person: "",
        email: "",
        telephone: "",
        physical_address: "",
        customer_type: "COMPANY",
      });
      setMessage(`Customer added: ${created.name}.`);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to create customer.");
    }
  };

  const handleSubmit = async () => {
    if (!selectedBusinessId || !selectedCustomerId) {
      setError("Please select a business and customer before saving the quotation.");
      return;
    }

    const payload = {
      business: Number(selectedBusinessId),
      customer: Number(selectedCustomerId),
      document_type: "QUOTATION",
      status: "draft",
      issue_date: issueDate,
      due_date: dueDate || null,
      notes,
      line_items: lineItems
        .filter((item) => item.description.trim())
        .map((item) => ({
          description: item.description.trim(),
          quantity: Number(item.quantity || 0),
          unit_of_measure: item.unit_of_measure || "hour",
          unit_price: Number(item.unit_price || 0),
          discount: Number(item.discount || 0),
          tax_rate: Number(item.tax_rate || 0),
        })),
    };

    setError("");
    setMessage("");
    setIsSubmitting(true);

    try {
      const result = await fetchJson<DocumentResponse>("/api/v1/documents/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setCreatedDocument(result);
      setDocuments((current) => [result as HistoryDocument, ...current]);
      setMessage(`Quotation saved successfully as ${result.document_number}.`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to save quotation.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <LayoutShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Quotations</p>
            <h2 className="mt-1 text-3xl font-semibold text-slate-900">Quotation builder</h2>
          </div>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
          >
            {isSubmitting ? "Saving..." : "Save quotation"}
          </button>
        </div>

        {error ? <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div> : null}
        {message ? <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div> : null}

        <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Quotation details</h3>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Business</label>
                  <select
                    value={selectedBusinessId}
                    onChange={(event) => setSelectedBusinessId(event.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                  >
                    {businesses.map((business) => (
                      <option key={business.id} value={String(business.id)}>{business.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Customer</label>
                  <select
                    value={selectedCustomerId}
                    onChange={(event) => setSelectedCustomerId(event.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                  >
                    {customers.length === 0 ? <option value="">No customers found</option> : null}
                    {customers.map((customer) => (
                      <option key={customer.id} value={String(customer.id)}>{customer.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Issue date</label>
                  <input type="date" value={issueDate} onChange={(event) => setIssueDate(event.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Expiry date</label>
                  <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" />
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Customer</h3>
                <button type="button" onClick={createCustomer} className="text-sm font-medium text-blue-600">Add customer</button>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Customer type</label>
                  <select value={customerForm.customer_type} onChange={(event) => setCustomerForm((current) => ({ ...current, customer_type: event.target.value as Customer["customer_type"] }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500">
                    <option value="COMPANY">Company</option>
                    <option value="INDIVIDUAL">Individual</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Name</label>
                  <input value={customerForm.name} onChange={(event) => setCustomerForm((current) => ({ ...current, name: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" placeholder="Customer name" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Contact person</label>
                  <input value={customerForm.contact_person} onChange={(event) => setCustomerForm((current) => ({ ...current, contact_person: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" placeholder="Primary contact" />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Telephone</label>
                  <input value={customerForm.telephone} onChange={(event) => setCustomerForm((current) => ({ ...current, telephone: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" placeholder="+27 00 000 0000" />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Email</label>
                  <input value={customerForm.email} onChange={(event) => setCustomerForm((current) => ({ ...current, email: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" placeholder="customer@example.com" />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-1.5 block text-sm font-medium text-slate-600">Address</label>
                  <textarea value={customerForm.physical_address} onChange={(event) => setCustomerForm((current) => ({ ...current, physical_address: event.target.value }))} className="min-h-20 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" placeholder="Customer postal or physical address" />
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">Line items</h3>
                <button type="button" onClick={addLineItem} className="text-sm font-medium text-blue-600">Add item</button>
              </div>

              <div className="space-y-4">
                {lineItems.map((item, index) => (
                  <div key={`${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="grid gap-3 md:grid-cols-[1.4fr_0.6fr_0.8fr_0.6fr]">
                      <input value={item.description} onChange={(event) => updateLineItem(index, "description", event.target.value)} placeholder="Description" className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" />
                      <input value={item.quantity} onChange={(event) => updateLineItem(index, "quantity", event.target.value)} placeholder="Qty" className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" />
                      <input value={item.unit_price} onChange={(event) => updateLineItem(index, "unit_price", event.target.value)} placeholder="Unit price" className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" />
                      <button type="button" onClick={() => removeLineItem(index)} className="rounded-xl border border-red-200 bg-red-50 px-2 py-2.5 text-sm font-medium text-red-700">Remove</button>
                    </div>

                    <div className="mt-3 grid gap-3 md:grid-cols-3">
                      <input value={item.unit_of_measure} onChange={(event) => updateLineItem(index, "unit_of_measure", event.target.value)} placeholder="Unit (hour, each, day)" className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" />
                      <input value={item.tax_rate} onChange={(event) => updateLineItem(index, "tax_rate", event.target.value)} placeholder="Tax %" className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" />
                      <input value={item.discount} onChange={(event) => updateLineItem(index, "discount", event.target.value)} placeholder="Discount" className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <label className="mb-1.5 block text-sm font-medium text-slate-600">Notes</label>
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} className="min-h-28 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500" placeholder="Scope of work, notes, conditions, acceptance criteria..." />
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <h3 className="text-lg font-semibold text-slate-900">Business info</h3>
              {selectedBusiness ? (
                <div className="mt-4 space-y-3 text-sm text-slate-600">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl text-sm font-bold text-white" style={{ backgroundColor: selectedBusiness.primary_brand_colour || "#2563EB" }}>
                      {selectedBusiness.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-semibold text-slate-900">{selectedBusiness.name}</div>
                      <div>{selectedBusiness.trading_name || "Trading name not supplied"}</div>
                    </div>
                  </div>
                  <div>{selectedBusiness.email || "No email saved"}</div>
                  <div>{selectedBusiness.telephone || "No phone saved"}</div>
                  <div>{selectedBusiness.physical_address || "No physical address saved"}</div>
                </div>
              ) : (
                <div className="mt-4 text-sm text-slate-500">Select a business to view saved information.</div>
              )}
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <h3 className="text-lg font-semibold text-slate-900">Quotation summary</h3>
              <div className="mt-4 space-y-3 text-sm text-slate-600">
                <div className="flex items-center justify-between"><span>Subtotal</span><span className="font-semibold text-slate-900">{formatCurrency(subtotal)}</span></div>
                <div className="flex items-center justify-between"><span>Discount</span><span className="font-semibold text-slate-900">-{formatCurrency(discountTotal)}</span></div>
                <div className="flex items-center justify-between"><span>Tax</span><span className="font-semibold text-slate-900">{formatCurrency(taxTotal)}</span></div>
                <div className="border-t border-slate-200 pt-3 text-base font-semibold text-slate-900 flex items-center justify-between"><span>Total</span><span>{formatCurrency(grandTotal)}</span></div>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <h3 className="text-lg font-semibold text-slate-900">Printed preview</h3>
              <div className="print-shell mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="print-page rounded-2xl bg-white p-6 shadow-sm">
                  <div className="mb-5 flex items-start justify-between border-b border-slate-200 pb-4">
                    <div>
                      <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Quotation</div>
                      <h4 className="mt-1 text-xl font-semibold text-slate-900">{createdDocument?.document_number ?? "Draft quotation"}</h4>
                    </div>
                    <div className="text-right text-sm text-slate-600">
                      <div>{selectedBusiness?.name ?? "Business name"}</div>
                      <div>{selectedBusiness?.email ?? "Email"}</div>
                    </div>
                  </div>

                  <div className="mb-5 grid gap-3 text-sm text-slate-600 md:grid-cols-2">
                    <div>
                      <div className="font-semibold text-slate-900">Customer</div>
                      <div>{customers.find((item) => String(item.id) === selectedCustomerId)?.name ?? "Select a customer"}</div>
                    </div>
                    <div>
                      <div className="font-semibold text-slate-900">Dates</div>
                      <div>Issued: {issueDate || "—"}</div>
                      <div>Expiry: {dueDate || "—"}</div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {lineItems.filter((item) => item.description.trim()).map((item, index) => {
                      const quantity = Number(item.quantity || 0);
                      const unitPrice = Number(item.unit_price || 0);
                      const discount = Number(item.discount || 0);
                      const taxable = quantity * unitPrice - discount;
                      const taxRate = Number(item.tax_rate || 0) / 100;
                      const total = taxable + taxable * taxRate;

                      return (
                        <div key={`${index}`} className="grid gap-2 border-b border-slate-200 pb-2 text-sm text-slate-700 md:grid-cols-[2fr_0.8fr_0.8fr_0.8fr_0.8fr]">
                          <div>{item.description}</div>
                          <div>{quantity} {item.unit_of_measure || "hour"}</div>
                          <div>{formatCurrency(unitPrice)}</div>
                          <div>{formatCurrency(discount)}</div>
                          <div>{formatCurrency(total)}</div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="mt-5 space-y-2 text-sm text-slate-700">
                    <div className="flex items-center justify-between"><span>Subtotal</span><span>{formatCurrency(subtotal)}</span></div>
                    <div className="flex items-center justify-between"><span>Discount</span><span>-{formatCurrency(discountTotal)}</span></div>
                    <div className="flex items-center justify-between"><span>Tax</span><span>{formatCurrency(taxTotal)}</span></div>
                    <div className="flex items-center justify-between border-t border-slate-200 pt-2 text-base font-semibold text-slate-900"><span>Total</span><span>{formatCurrency(grandTotal)}</span></div>
                  </div>
                </div>
              </div>

              <button type="button" onClick={() => window.print()} className="mt-6 w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 transition hover:bg-slate-50">
                Print / save as PDF
              </button>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/50">
              <h3 className="text-lg font-semibold text-slate-900">Quotation history</h3>
              <div className="mt-4 space-y-3">
                {documents.length === 0 ? (
                  <div className="text-sm text-slate-500">No quotations saved for this business yet.</div>
                ) : (
                  documents.slice(0, 5).map((document) => (
                    <div key={document.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-slate-900">{document.document_number}</span>
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-emerald-700">{document.status}</span>
                      </div>
                      <div className="mt-1 text-slate-600">{document.customer_name}</div>
                      <div className="mt-2 flex items-center justify-between text-slate-500">
                        <span>{document.issue_date}</span>
                        <span>{formatCurrency(Number(document.total || 0))}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </LayoutShell>
  );
}
