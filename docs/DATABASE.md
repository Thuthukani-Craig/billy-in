# Billy-in Database Design

## Core entities

### Business

Stores business profile details, branding, accounting configuration, and document numbering state.

### Customer

Stores customer names, contact details, customer type, and the business association.

### Document

Supports quotation, invoice, and receipt records with line items and financial totals.

### Payment

Represents a recorded real payment and links to the receipt or invoice context.

## Key constraints

- A document must be associated with a valid business.
- A customer must belong to the same business as the document.
- Business numbering is tracked independently for quotation, invoice, and receipt sequences.
- Historical document data is retained even if a customer profile is edited later.

## Local database

The default local configuration uses SQLite to keep the setup lightweight and easy for development.

## Production readiness

The project is intentionally designed so that a PostgreSQL configuration can be introduced later without reworking the application domain layer.
