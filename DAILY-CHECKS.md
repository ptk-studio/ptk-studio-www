# DAILY-CHECKS: Mochi Factory site (mochi-factory.com)

What is checked every day (R97; the standard is in the hub's `project-groups/AGENTS.md` → 'Daily checks'). The worker runs these in its first sweep of the day and writes the results into the manager's daily analytics; a major problem goes to the Owner the same sweep.

| Check | Where | Healthy looks like | If not, do this | Who |
|---|---|---|---|---|
| New user feedback (R64) | 88eggs Feedback inbox for this project; the hub feedback digest | every message read within a day | reply or file a Task; a bug report goes to the manager the same sweep | mm1-worker1 (first sweep of the day) · read by mm1-manager1 |
| Site up and redirects | `https://mochi-factory.com/` + `python3 _tools/check-redirects.py` | HTTPS 200; 66 of 66 old URLs redirect and resolve | tell the manager; the App Store privacy/support URLs depend on it | mm1-worker1 (first sweep of the day) · read by mm1-manager1 |
| Certificate expiry | `https://mochi-factory.com` (and ptk-studio.com redirect) | > 14 days | tell the director (DNS/Cloudflare) | mm1-worker1 (first sweep of the day) · read by mm1-manager1 |
