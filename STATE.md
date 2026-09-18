# OncoAI - Project State & Operational Log

## 1. Active Infrastructure & Endpoints
* **Frontend / Dashboard:** Vercel (`syncplus-app.vercel.app`)
* **Core SaaS Backend:** Google Cloud Run (`https://oncoaisaas-930868454014.us-central1.run.app`)
* **Database & Services:** Railway (Production PostgreSQL backend)
* **Redundant Services:** Render service (`OncoAI-SaaS`) suspended to eliminate monthly overhead.

## 2. Compliance & Security Guardrails
* **Audit Logging:** 21 CFR Part 11 compliant audit backend (`audit_backend.py`) operational.
* **Storage Mirroring:** Immutable audit events backed by Google Cloud Storage (GCS) with cryptographic checksum verification.

## 3. Active Submissions & Milestones
* **Google for Startups Cloud Program:** Application update submitted (September 16, 2026) featuring the active Cloud Run production endpoint for re-evaluation. Awaiting review window response (3–5 business days).
* **Shopify App Store:** `syncplus-app` submitted and currently in the review queue.

## 4. Upcoming Timeline & Logistics
* **Travel Window:** Departure for Mohali scheduled for October 24, 2026.
* **Operational Mode:** Remote-only management via GCP CLI, Cloud Console, and GitHub integration.
