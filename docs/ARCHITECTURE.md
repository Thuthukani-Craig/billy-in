# Billy-in Architecture

## Overview

Billy-in is organized as a modular monorepo with a Django REST API backend and a Next.js frontend. The design seeks to keep domain logic in the backend and preserve a clean separation between data, validation, and presentation.

## Backend modules

- `accounts`: authentication and user-related service support
- `businesses`: business records and operational configuration
- `customers`: customer records and relationship validation
- `documents`: quotations, invoices, receipts, and document numbering logic
- `payments`: payment records and associated financial movement
- `reporting`: summary and analytical endpoints

## Frontend modules

The frontend is structured around business-oriented pages:

- Dashboard
- Businesses
- Customers
- Quotations
- Invoices
- Receipts
- Payments
- Reports
- Settings

## Design principles

- Single-admin model, not multi-tenant SaaS
- Shared business context without duplicating logic
- Decimal-based monetary calculations on the backend
- API versioning under `/api/v1/`
- Validation of business-customer relationships at the model/serializer layer
- SQLite for local development and PostgreSQL-ready configuration for production

## Security posture

- Secret values are loaded from environment variables
- CORS and CSRF are configured explicitly
- The system encourages Django admin authentication for administrative access
- A defensive approach is used for document access and related validation

## Current status

This repository currently focuses on a working foundation, with core business and customer management implemented and the API structure established for future expansion.
