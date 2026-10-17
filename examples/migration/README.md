# Fictional historical migration examples

All names, identifiers, contact details and narratives in this folder are invented. These files are for a test organisation, not real provider onboarding. Documents are visibly marked fictional and are not valid evidence or certificates.

Use source system **Legacy demo** for every related structured file. Configure First Aid, CPR and Worker Screening credential types using the commands in the main migration README.

1. Import and approve history/01_staff_history.csv (3 staff).
2. Import and approve history/02_participants_history.csv (2 participants).
3. Import and approve history/03_credentials_history.csv (3 pending credentials).
4. Import and approve history/04_incidents_history.csv (2 incidents).
5. Import and approve history/05_complaints_history.csv (1 complaint).
6. Import and approve history/06_risks_history.csv (2 risks).

The first six files total 13 live records. Approved staff/participants now appear on Workers and Participants, and the dashboard shows actual record totals. Migration live-record tabs remain available for reconciliation.

Then try review_cases/07_staff_needs_review.csv: on that baseline it has 1 ready, 1 duplicate, 3 invalid. Approve the ready row without importing the unresolved rows. Correct or skip the others with recorded reasons. review_cases/08_staff_reviewed_update.csv demonstrates an explicit update to the existing S-001 UUID.

history/09_provider_columns_staff.csv and .xlsx are alternatives containing the same two additional staff. Import one only. Map columns using history/09_column_mapping.json. Choose DD/MM/YYYY for CSV text dates; XLSX has native Excel dates. The mapping JSON is a guide for the mapping screen, not an importable record file.

review_cases/10_incident_bad_dates.csv must remain invalid. review_cases/11_duplicate_headers.csv must be rejected before staging.

Documents are uploaded individually through Documents & versions. Use policy_v1_2024.pdf then policy_v2_2026.docx as versions of the same document, with dates entered from their contents. Upload first_aid_expired_C001.pdf against the C-001 credential. Upload the historical incident PDF or scanned PNG against INC-2024-001. The PNG is a generated scan-style rendition for image upload testing, not an authentic scanned/signed record. No document/image text extraction is performed.

See docs/data-migration/README.md for the complete walkthrough, metadata dates and expected results. templates/ contains canonical blank CSV headers for the six import types.
