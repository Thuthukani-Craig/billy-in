"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { getStoredActiveBusiness } from "@/lib/api";

const navGroups = [
  { title: "Workspace", items: [{ href: "/", label: "Overview", icon: "◫" }, { href: "/businesses", label: "Businesses", icon: "▦" }, { href: "/customers", label: "Customers", icon: "♙" }] },
  { title: "Revenue", items: [{ href: "/quotations", label: "Quotations", icon: "▤" }, { href: "/invoices", label: "Invoices", icon: "▧" }, { href: "/receipts", label: "Receipts", icon: "▣" }, { href: "/payments", label: "Payments", icon: "↗" }] },
  { title: "Insights", items: [{ href: "/reports", label: "Reports", icon: "⌁" }] },
  { title: "Manage", items: [{ href: "/settings", label: "Settings", icon: "⚙" }] },
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
    <div className="min-h-screen bg-[#f4f6fa] text-slate-900">
      <div className="mx-auto flex min-h-screen max-w-[1800px] flex-col lg:flex-row">
        <aside className="z-10 w-full shrink-0 border-b border-slate-200/80 bg-white lg:sticky lg:top-0 lg:h-screen lg:w-[248px] lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3 border-b border-slate-100 px-6 py-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-base font-semibold text-white shadow-sm">b.</div>
            <div><div className="text-[15px] font-semibold tracking-tight text-slate-950">Billy-in</div><div className="mt-0.5 text-[11px] text-slate-400">Business finance, clearly.</div></div>
          </div>

          <div className="px-4 py-5">
            <div className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">Current business</div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3">
              <div className="flex items-center gap-2.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 text-xs font-bold text-blue-700">{activeBusinessName ? activeBusinessName.slice(0, 1).toUpperCase() : "—"}</span>
                <div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-800">{activeBusinessName ?? "All businesses"}</p><p className="mt-0.5 text-[11px] text-slate-400">Business workspace</p></div>
              </div>
            </div>
          </div>

          <nav className="space-y-6 px-3 pb-6">
            {navGroups.map((group) => (
              <div key={group.title}>
                <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">{group.title}</p>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const isActive = pathname === item.href;
                    const isComingSoon = ["/invoices", "/receipts", "/payments", "/reports", "/settings"].includes(item.href);
                    return (
                      <Link key={item.href} href={item.href} className={["flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition", isActive ? "bg-blue-50 text-blue-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"].join(" ")}>
                        <span className={["w-5 text-center text-base", isActive ? "text-blue-600" : "text-slate-400"].join(" ")} aria-hidden="true">{item.icon}</span>
                        <span className="flex-1">{item.label}</span>
                        {isComingSoon ? <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-slate-400">Soon</span> : null}
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
          <div className="hidden border-t border-slate-100 px-6 py-4 lg:block">
            <p className="text-[11px] text-slate-400">A clearer view of your business.</p>
            <p className="mt-1 text-[10px] text-slate-300">Billy-in · Private workspace</p>
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          <header className="sticky top-0 z-[5] border-b border-slate-200/70 bg-white/90 backdrop-blur-xl">
            <div className="flex min-h-[72px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-9">
              <div><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">Financial workspace</p><h1 className="mt-1 text-sm font-semibold text-slate-800">{navGroups.flatMap((group) => group.items).find((item) => item.href === pathname)?.label ?? "Billy-in"}</h1></div>
              <div className="flex items-center gap-3">
                <div className="hidden text-right sm:block"><p className="text-xs font-medium text-slate-700">Administrator</p><p className="mt-0.5 text-[10px] text-slate-400">Private workspace</p></div>
                <div className="flex h-9 w-9 items-center justify-center rounded-full border border-blue-100 bg-blue-50 text-xs font-semibold text-blue-700">AD</div>
              </div>
            </div>
          </header>
          <div className="p-4 sm:p-6 lg:p-9">{children}</div>
        </main>
      </div>
    </div>
  );
}
