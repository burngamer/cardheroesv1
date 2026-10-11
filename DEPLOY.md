# Card Heroes — Going Public (GitHub + Render + Google Drive)

Follow the steps in order. Total time: about 45 minutes the first time.

---

## 0. Before anything: your OLD GitHub repo

Your previous repo `github.com/burngamer/card-heroes` contains `db.sqlite3`, the old admin
password inside `create_admin.py`, and `context_card_heroes.md`. If it is public:

1. GitHub → that repo → **Settings → General → Danger Zone → Change visibility → Private**
   (or delete the repo).
2. Treat the old `captain` password as burned. The new site never uses it — the production
   admin is created from a **new** password you choose in step 4.

`ch_v1` starts with a clean history, and its `.gitignore` keeps the database, media,
secrets and the context notes out of GitHub.

---

## 1. Test it on your computer

```powershell
cd C:\Users\kmpou\Desktop\ch_v1
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts\compile_translations.py
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000 and check:

- The flag pill sits in the bottom-left corner. Click **ΕΛ** and the whole site switches to Greek.
  Click **EN** to switch back. (A first-time visitor whose browser is set to Greek gets Greek automatically.)
- Your old local data (cards, the local `captain` account) still works in this copy.

> The copy brought `db.sqlite3` and `media/` along for local testing. Neither goes to GitHub.

---

## 2. Google Drive (where card images will live)

Images are uploaded to a folder in **your** Google Drive and shown to visitors straight from
Google, so the web server stores and serves none of them. (Render's free server also deletes any
uploaded file on every restart, so this is required, not just nice to have.)

### 2a. Create the Google credentials (one time, ~10 min)

1. Go to https://console.cloud.google.com → top bar → **New project** → name it `Card Heroes` → Create.
2. **APIs & Services → Library** → search **Google Drive API** → **Enable**.
3. **Google Auth Platform** (older UI: *OAuth consent screen*):
   - **Branding**: app name `Card Heroes`, your email as support + developer contact. Save.
   - **Audience**: User type **External**. Then click **Publish app** so the status says
     **In production**.
     ⚠ If you leave it in *Testing*, Google expires the token after **7 days** and image
     uploads will suddenly stop working.
   - **Data access** (scopes): add `.../auth/drive.file` ("See, edit, create and delete only the
     specific Google Drive files you use with this app").
4. **Clients** (older UI: *Credentials → Create credentials → OAuth client ID*):
   - Application type: **Desktop app**, name `Card Heroes uploader` → Create.
   - Click **Download JSON**. Rename the file to `client_secret.json` and put it in the
     `ch_v1` folder, next to `manage.py`. (It's git-ignored, so it won't reach GitHub.)

### 2b. Get your four GDRIVE values

```powershell
cd C:\Users\kmpou\Desktop\ch_v1
venv\Scripts\activate
python scripts\gdrive_setup.py
```

A browser opens. Sign in with the Google account that should hold the images.
You'll likely see **"Google hasn't verified this app"**. That's normal for a private app you
made yourself: click **Advanced → Go to Card Heroes (unsafe)** → **Continue**.

The script creates a **Card Heroes Media** folder in that Drive and prints:

```
GDRIVE_CLIENT_ID=...
GDRIVE_CLIENT_SECRET=...
GDRIVE_REFRESH_TOKEN=...
GDRIVE_FOLDER_ID=...
```

Keep these somewhere safe (a password manager). They go into Render in step 4.

> The site only gets the `drive.file` permission: it can see **only the files it uploaded itself**,
> never the rest of your Drive. Don't move or rename the Card Heroes Media folder.

---

## 3. Put the code on GitHub

1. https://github.com/new → name `card-heroes-v1` → **Private** → don't add a README → Create.
2. In PowerShell:

```powershell
cd C:\Users\kmpou\Desktop\ch_v1
git init
git add .
git status          # sanity check: NO db.sqlite3, media/, venv/, client_secret.json, .env
git commit -m "Card Heroes v1: Greek/English, production settings, Google Drive storage"
git branch -M main
git remote add origin https://github.com/burngamer/card-heroes-v1.git
git push -u origin main
```

If `git status` lists any of the files from the sanity-check line, stop and don't commit.

---

## 4. Deploy on Render

1. https://dashboard.render.com → **New → Blueprint** → connect GitHub → pick `card-heroes-v1`.
2. Render reads `render.yaml` and proposes **card-heroes** (web service) + **card-heroes-db** (Postgres).
3. It asks for the secret values. Fill in:

| Variable | Value |
|---|---|
| `DJANGO_ADMIN_URL` | a hard-to-guess path, e.g. `harbor-control-7319/` (your Django admin will live there) |
| `DJANGO_SUPERUSER_USERNAME` | your admin username |
| `DJANGO_SUPERUSER_EMAIL` | your email |
| `DJANGO_SUPERUSER_PASSWORD` | a **new**, strong password (10+ characters, not the old one) |
| `GDRIVE_CLIENT_ID` / `GDRIVE_CLIENT_SECRET` / `GDRIVE_REFRESH_TOKEN` / `GDRIVE_FOLDER_ID` | from step 2b |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | see step 6, or leave empty for now |

`DJANGO_SECRET_KEY` and `DATABASE_URL` are filled in automatically.

4. **Apply**. The first build takes ~3–5 minutes. Watch the **Logs** tab for
   `Admin "<you>" created.` and finally `Your service is live`.
5. Your site: `https://card-heroes.onrender.com` (or whatever name Render shows).

---

## 5. After the first deploy, check:

- [ ] Home page loads over **https**, and the flag pill switches EN ⇄ ΕΛ
- [ ] Log in with your new admin → **Dashboard** appears in the navbar
- [ ] Dashboard shows **no** yellow "Google Drive is not configured" warning
- [ ] Add a card with a front + back photo, then check that the image shows on the site, a file appears in
      **Card Heroes Media** in your Drive, and the flip and magnify buttons work
- [ ] Edit the card and replace the photo; the old file disappears from Drive
- [ ] `https://<your-site>/<DJANGO_ADMIN_URL>` opens the Django admin
- [ ] Register a test customer, add to cart, check out, then delete the test data

The live database starts **empty**. Add your real cards through the dashboard. (The demo cards
are intentionally not loaded in production.)

---

## 6. Email (password-reset links) — Gmail

Without this, reset emails only appear in Render's logs.

1. Your Google account → **Security** → turn on **2-Step Verification**.
2. https://myaccount.google.com/apppasswords → create one named `Card Heroes` → copy the 16 characters.
3. Render → card-heroes → **Environment**:
   `EMAIL_HOST=smtp.gmail.com`, `EMAIL_HOST_USER=you@gmail.com`,
   `EMAIL_HOST_PASSWORD=<the 16 characters>`, `DEFAULT_FROM_EMAIL=Card Heroes <you@gmail.com>`
   → **Save, rebuild and deploy**.

---

## 7. ⚠ The free database is deleted after 30 days

Render deletes **free** Postgres databases 30 days after creation, with 14 days of grace to upgrade
before everything is erased. Before day 30, pick one:

- **Upgrade it** in Render (card-heroes-db → change plan to a paid one). This is the simplest option.
- **Or use a free Postgres that doesn't expire** (e.g. Neon): create a database there, copy
  its connection string (ends with `?sslmode=require`), then in Render set
  `DATABASE_URL` on the web service to that string. Do this **before** you add real data,
  or export/import your data first.

Also on the free plan the site **sleeps after 15 minutes without visitors**, so the first visit
after that takes about 50 seconds. The paid web plan removes the sleep.

---

## 8. Before you call it a real shop

- **Image rights:** `welcome-bg.png` (shows Mickey Mouse) and `onepiece-bg.png` are characters
  owned by Disney and Shueisha/Toei. Selling genuine cards is normal, but using official artwork
  as website decoration on a public commercial site is a copyright risk. Make sure you have the
  right to use these images, or swap them for licensed or original art.
- **Privacy (GDPR):** checkout collects names, emails and addresses, so you'll need a privacy policy
  page. Fonts load from Google Fonts and images from Google, which also shares visitor IPs with
  Google. Mention that in the policy, or self-host the fonts.
- **Payments:** checkout is still a demo (orders are marked Paid with no payment). Keep the demo
  notices until a real payment provider is added.
- **Login brute-force protection:** worth adding next (e.g. `django-axes`) now that the login
  and admin pages are public.
- **Own domain:** add it in Render → Settings → Custom Domains, then add it to
  `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` (with `https://`). Once it has
  worked over HTTPS for a while, set `DJANGO_HSTS_SECONDS=31536000`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build fails at `bash build.sh` with `\r: command not found` | The file got Windows line endings. `.gitattributes` prevents this. Re-run `git add --renormalize .`, commit and push. |
| `DisallowedHost` / 400 Bad Request | Using a custom domain? Add it to `DJANGO_ALLOWED_HOSTS`. |
| 403 CSRF error on forms | Add your domain to `DJANGO_CSRF_TRUSTED_ORIGINS` with `https://`. |
| Uploads work, then fail after a week with `invalid_grant` | The Google app is still in *Testing*. Publish it (step 2a.3), run `scripts/gdrive_setup.py` again, and paste all four new values into Render. Old images keep working. |
| Images show a broken icon | Check the Drive file is shared "Anyone with the link". If Google changed its image URLs, set `GDRIVE_URL_TEMPLATE=https://drive.google.com/thumbnail?id={id}&sz=w2000`. |
| Locked out of admin | In Render → Shell: `python manage.py create_admin --reset-password` (uses the env password). |
| Changed a Greek text | Edit `locale/el/LC_MESSAGES/django.po`, push. The build compiles it. |
