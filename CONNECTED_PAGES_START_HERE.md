# Connected-page installation notes

For the latest cumulative overlay, use **Kind_Compliance_Design_Restored.zip** and follow [the design-restoration guide](docs/data-migration/DESIGN_RESTORATION.md). It includes the connected pages and startup fix; do not reapply an older overlay afterwards.

Previously approved imports will appear automatically on Workers and Participants. Accepted documents appear in Documents; pending originals are under Awaiting sign-off. There is no need to re-import existing records.

Read docs/data-migration/CONNECTED_PAGES.md for profile edits, original uploads, document replacement, credential verification, account linking, assigned participant access, test steps and known limits. The full suite currently has 79 passing tests on SQLite test databases; PostgreSQL/browser checks still need to be run locally.
