import { LayoutShell } from "@/components/layout-shell";

export default function SettingsPage() {
  return (
    <LayoutShell>
      <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm shadow-slate-200/50">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Settings</div>
        <h2 className="mt-3 text-3xl font-semibold text-slate-900">Coming soon</h2>
        <p className="mt-3 text-slate-600">Business account preferences, branding, and defaults will be managed here.</p>
      </div>
    </LayoutShell>
  );
}
