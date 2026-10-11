# Card Heroes (v1)

A Django store for **One Piece** and **Lorcana** collector's cards — bilingual (English / Ελληνικά),
light/dark themes, reviews, staff dashboard, and card images stored on Google Drive.

**Going public?** Follow [DEPLOY.md](DEPLOY.md) step by step.

## Run locally

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts\compile_translations.py
python manage.py migrate
python manage.py seed_cards        # optional demo cards (local only)
python manage.py runserver
```

No configuration is needed locally: DEBUG is on, data is in SQLite, images are saved to `media/`.
To create an admin locally, set `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_PASSWORD`
and run `python manage.py create_admin` (or use `python manage.py createsuperuser`).

## Features

- Catalog with search, rarity/set/price/stock filters and sorting
- Card pages with 3D flip (front/back), magnifier, star reviews and comments
- Session cart and demo checkout (live price, stock-locked: no overselling)
- Accounts, profile, order history, email password reset
- Staff dashboard: stats, order status, card CRUD with front/back uploads, user management
- **English / Greek switch**: flag pill bottom-left on every page; auto-detects the browser language
- **Google Drive image storage** in production (see `shop/storage.py`)

## Translations

Greek texts live in `locale/el/LC_MESSAGES/django.po`. After editing, run
`python scripts/compile_translations.py` (pure Python, no gettext install needed).
New text in templates: wrap it in `{% translate "..." %}` and add a matching entry to the `.po` file.

## Configuration

All settings come from environment variables. See [.env.example](.env.example).
