#!/usr/bin/env bash
# Render build script — runs on every deploy.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Greek/English: compile locale/*.po -> .mo (pure Python, no gettext needed)
python scripts/compile_translations.py

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Create the admin account on first deploy (only if the env vars are set).
# Existing accounts are never overwritten, so changing your password in the site sticks.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py create_admin
fi
