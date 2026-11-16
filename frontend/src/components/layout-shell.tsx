"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { getStoredActiveBusiness } from "@/lib/api";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/businesses", label: "Businesses" },
  { href: "/customers", label: "Customers" },
  { href: "/quotations", label: "Quotations" },
  { href: "/invoices", label: "Invoices" },
  { href: "/receipts", label: "Receipts" },
  { href: "/payments", label: "Payments" },
  { href: "/reports", label: "Reports" },
  { href: "/settings", label: "Settings" },
] as const;

export function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [activeBusinessName, setActiveBusinessName] = useState<string | null>(null);

  useEffect(() => {
    const syncActiveBusiness = () => {
      const business = getStoredActiveBusiness();
      setActiveBusinessName(business ? business.name : null);
    };

    syncActiveBusiness();
    window.addEventListener("storage", syncActiveBusiness);
    return () => window.removeEventListener("storage", syncActiveBusiness);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-200 bg-white lg:w-72 lg:border-b-0 lg:border-r">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-600">Billy-in</div>
              <div className="mt-1 text-lg font-semibold text-slate-900">Operations</div>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white">B</div>
          </div>

          <div className="px-4 py-5">
            <div className="mb-4 px-3 text-[11px] font-medium uppercase tracking-[0.16em] text-slate-400">Active business</div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-sm font-semibold text-slate-900">{activeBusinessName ?? "No business selected"}</div>
              <div className="mt-1 text-xs text-slate-500">Current workspace</div>
            </div>
          </div>

          <nav className="space-y-1 px-3 pb-6">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const isComingSoon = ["/invoices", "/receipts", "/payments", "/reports", "/settings"].includes(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "flex items-center justify-between rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive ? "bg-blue-600 text-white shadow-sm" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                  ].join(" ")}
                >
                  <span>{item.label}</span>
                  {isComingSoon ? (
                    <span className="rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
                      soon
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="flex-1">
          <header className="border-b border-slate-200 bg-white/90 backdrop-blur-sm">
            <div className="flex flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between lg:px-8">
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Business workspace</div>
                <h1 className="mt-1 text-2xl font-semibold text-slate-900">Billy-in</h1>
              </div>

              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-400">Period</div>
                  <div className="text-sm font-semibold text-slate-700">This month</div>
                </div>
                <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">AC</div>
                  <div>
                    <div className="text-sm font-semibold text-slate-900">Administrator</div>
                    <div className="text-xs text-slate-500">Manager</div>
                  </div>
                </div>
              </div>
            </div>
          </header>

          <div className="p-4 lg:p-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
