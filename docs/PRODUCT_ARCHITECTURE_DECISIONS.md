# Billy-in Product Architecture Decisions

**Status:** Accepted direction for the current build  
**Scope:** Private multi-business use first; commercial SaaS may follow later.

## Product direction

Billy-in will initially serve the businesses managed by one administrator. The architecture must not assume that every future user belongs to only one business, or that business data can be shared across customers. We will build sound tenant boundaries now, while deliberately postponing public registration, subscription billing, plans, and SaaS marketing features.

## Tenant and business boundaries

- A tenant is the data-ownership boundary. A business is an operating entity inside a tenant.
- A user may eventually belong to more than one tenant, with a role per membership.
- Never silently choose the first active membership when a request needs tenant context.
- Resolve the active tenant explicitly from an authenticated, validated context; verify membership on every request.
- Scope every business, customer, supplier, document, payment, expense, and report query to the authorised tenant.
- Validate that related records belong to the same tenant and, where required, the same business.
- Keep platform-level administration separate from tenant owner/admin/manager/viewer roles.
- Do not add public sign-up or SaaS billing in this phase.

## Financial integrity

- Use Decimal values for all monetary calculations; never use floating-point arithmetic for persisted financial values.
- Treat issued financial documents and recorded payments as auditable records.
- Payment allocation must update invoice paid and outstanding balances through one transactional domain operation.
- Support partial payments, full settlement, overpayments only where an explicit allocation policy permits them, and reversals/voids through auditable correction records rather than silent deletion.
- A future accounting ledger must be the source of truth for financial statements. Do not present revenue less expenses as accounting profit until the required accounting rules and entries exist.
- Reports must be based on persisted records and tenant/business scope, not demonstration constants.

## Document lifecycle and PDF output

- Quotations, invoices, and receipts share reusable document data and rendering infrastructure, while retaining their own lifecycle rules and numbering sequences.
- Generate PDFs as downloadable digital files. Do not rely on `window.print()` or the browser print dialog as the primary export path.
- Preview and PDF output must use the same rendering rules and data.
- Document numbering must be generated safely under concurrent requests and be unique within the agreed business/tenant scope.
- Once a document is issued, preserve the issued financial facts and a rendering/style snapshot (or immutable generated artifact). Later edits to a business profile or template must not silently rewrite a previously issued document.
- Validate South African tax and invoice requirements against current authoritative guidance before describing a document as SARS-compliant.

## Document template system

Templates are presentation-only. They must never change line items, calculations, tax, totals, payment allocations, or accounting records.

Initial visual themes to design:
1. Classic
2. Modern
3. Minimal
4. Corporate
5. Bold
6. Industrial

A business should be able to select defaults independently for quotations, invoices, and receipts. Template settings may include logo, supported brand colours, typography choices, optional display fields, payment instructions, and terms. Keep theme definitions versioned and constrained to supported design tokens; do not store arbitrary executable HTML or CSS supplied by users.

## Build sequence

1. Audit and test the existing application before changing domain behaviour.
2. Correct tenant-context resolution and enforce tenant/business ownership at API query and write boundaries.
3. Complete document numbering and document lifecycle rules.
4. Implement transactional payment allocation and invoice balance updates.
5. Implement server-generated downloadable PDFs and a shared preview/rendering layer.
6. Add versioned document themes and per-document-type business defaults.
7. Add expenses and suppliers.
8. Build the accounting ledger and reports on top of verified financial events.
9. Add bank reconciliation, export/backup controls, and operational hardening.
10. Only when the private product is stable, plan public onboarding and SaaS billing.

## Change and release controls

- Work on feature branches and use pull requests.
- Do not merge to the default branch, deploy, or alter production data without explicit approval.
- Do not reset or replace an existing database as part of routine development.
- Add tests for tenant isolation, monetary calculations, document numbering, payment allocation, and PDF generation.
- Record what was actually tested. A code inspection is not a passing test.
