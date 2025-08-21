# UX_FLOW

Sessionless quickstart
1. User visits / -> clicks Start
2. UI shows a simple pay/topup CTA; after simulated payment, server returns session_token and redirects to /d/<token>
3. Dashboard shows balance, Add Target form, and explanation: "Save this link or download token; we do not store your email."

Dashboard pages
- /d/<token> (main): list of watchers (targets), balance, top-up button, export token, receipts
- /d/<token>/target/<wid>: per-target history, last N checks, toggle enabled, delete
- Admin /admin/earnings protected by admin.key

Receipts
- Each topup and consume generates a small JSON receipt file user can download

Recovery
- User can present a receipt id to re-create session_token (server validates ledger entry and returns a new token linked to that ledger)."