# Hosted PostgreSQL (Option C)

Racecoe stores the Ergast historical archive in **PostgreSQL** (`f1.*` tables). Chat sessions can live in `chat.*` on the same database. The app **does not** need Kaggle or local CSVs on each machine once the archive is loaded.

## How it works

1. You create a **hosted Postgres** instance (Render, Neon, or Supabase).
2. You set **`DATABASE_URL`** on the web service (and locally in `.env` for development).
3. On **first boot**, `utils/runtime_boot.py`:
   - applies `db/schema.sql`
   - loads `data/historical_csvs/` into `f1.*` if `f1.races` is empty
4. All historical questions (e.g. Hamilton 2012 team) query **SQL**, not pandas files.

Verify after deploy:

```http
GET /api/health
```

Look for:

```json
"database": {
  "database_url_set": true,
  "historical_using_postgres": true,
  "archive_rows": 1100,
  "reachable": true
}
```

(`archive_rows` is approximate; any value **> 0** means the archive loaded.)

---

## A. Render (same provider as racecoe.onrender.com)

**Blueprint (recommended)** — repo includes `render.yaml`:

- Provisions **`racecoe-db`** (Postgres 16)
- Injects `DATABASE_URL` into the **`racecoe`** Docker web service
- Sets `HISTORICAL_BACKEND=postgres` and `SESSION_STORE=postgres`

**Dashboard steps**

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** → connect this GitHub repo (or sync an existing Blueprint).
2. Set secret env vars on the **web** service: `GEMINI_API_KEY`, `HF_TOKEN`, optional `CORS_ORIGINS`.
3. Deploy. **First deploy** may take several minutes while the archive loads (watch **Logs** for `[boot] Postgres archive load complete`).
4. Open `https://<your-service>.onrender.com/api/health` and confirm `historical_using_postgres` is true.

**Already deployed without a database?**

1. Create **PostgreSQL** → name it `racecoe-db` (or any name).
2. On the **web** service → **Environment** → add `DATABASE_URL` from the DB **Internal** or **External** connection string.
3. Set `HISTORICAL_BACKEND=postgres` and `SESSION_STORE=postgres`.
4. **Manual Deploy** → wait for boot logs.

Render Postgres is **paid** (no free DB tier). The web service can stay on the free plan; the database is billed separately.

---

## B. Neon (serverless Postgres)

1. [neon.tech](https://neon.tech) → create project → copy the **connection string** (use the pooled URL for serverless apps if you prefer).
2. Ensure the URL includes TLS, e.g. `?sslmode=require` (Racecoe adds this automatically for `*.neon.tech` hosts).
3. In `.env`:

   ```env
   DATABASE_URL=postgresql://user:pass@ep-....neon.tech/neondb?sslmode=require
   HISTORICAL_BACKEND=postgres
   SESSION_STORE=postgres
   ```

4. **One-time load** from your machine (CSV files stay in the repo; only SQL is stored in Neon):

   ```bash
   python scripts/bootstrap_hosted_db.py
   ```

5. On **Render** (or any host), set the **same** `DATABASE_URL` and redeploy. Boot will see existing rows and skip reload.

---

## C. Supabase

1. Project → **Settings** → **Database** → connection string (URI).
2. Use **Session mode** or **Transaction pooler** URI; add `sslmode=require` if not present.
3. Same as Neon: `.env` → `python scripts/bootstrap_hosted_db.py` → set env on production → deploy.

---

## Local API against hosted DB

```bash
cp .env.example .env
# DATABASE_URL=...  (hosted)
# HISTORICAL_BACKEND=postgres
# SESSION_STORE=postgres

python scripts/bootstrap_hosted_db.py   # first time only
python server.py                      # http://127.0.0.1:5001
```

Frontend dev: `cd frontend && npm run dev` (proxies `/api` to port 5001).

---

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| Chat says CSV / `setup_historical_data` | `DATABASE_URL` missing on the **running** service, or archive empty. Run bootstrap or redeploy with Postgres env vars. |
| `historical_using_postgres: false` | Set `HISTORICAL_BACKEND=postgres` or load `f1.races` so `auto` picks Postgres. |
| SSL errors (Neon/Supabase) | Use `sslmode=require` in the URL. |
| Boot timeout on Render free tier | First archive load is heavy; check logs; consider a longer health check start period or run `bootstrap_hosted_db.py` before deploy. |
| Fallback to CSV in logs | Postgres unreachable at boot — fix URL/network; app continues on CSV until you fix DB. |

---

## Security

- Never commit `.env` or paste production `DATABASE_URL` in chat/issues.
- Use Render **internal** database URLs between Render services when both run on Render.
- Rotate DB passwords if a URL leaks.
