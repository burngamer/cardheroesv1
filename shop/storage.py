"""Google Drive storage for uploaded card images.

When the GDRIVE_* environment variables are set, Django's default file storage
becomes this class (see settings.STORAGES). Every image uploaded through the
dashboard or the Django admin is:

  1. downscaled if it is huge (GDRIVE_MAX_DIMENSION, default 2000px),
  2. uploaded to your Google Drive folder,
  3. shared as "anyone with the link can view",
  4. stored in the database as  gdrive/<file-id>/<filename>.

Visitors' browsers then load the picture straight from Google
(https://lh3.googleusercontent.com/d/<file-id>), so the images never touch
the web server's disk or bandwidth.

Auth uses an OAuth refresh token for YOUR Google account (service accounts
have no Drive storage quota of their own). Get the token with
scripts/gdrive_setup.py. Scope is drive.file: the site can only see files it
created itself — never the rest of your Drive.
"""
import io
import logging
import mimetypes
import os
import threading

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_URI = 'https://oauth2.googleapis.com/token'
PREFIX = 'gdrive/'
RESIZABLE = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}

_local = threading.local()   # googleapiclient service objects are not thread-safe


def _service():
    service = getattr(_local, 'service', None)
    if service is None:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials(
            token=None,
            refresh_token=settings.GDRIVE_REFRESH_TOKEN,
            token_uri=TOKEN_URI,
            client_id=settings.GDRIVE_CLIENT_ID,
            client_secret=settings.GDRIVE_CLIENT_SECRET,
            scopes=SCOPES,
        )
        service = build('drive', 'v3', credentials=creds, cache_discovery=False)
        _local.service = service
    return service


def _file_id(name):
    """'gdrive/<id>/<filename>' -> '<id>'; anything else -> None."""
    if name and name.startswith(PREFIX):
        parts = name[len(PREFIX):].split('/', 1)
        return parts[0] or None
    return None


def _downscale(raw, filename):
    """Return (bytes, mimetype) — shrunk if bigger than GDRIVE_MAX_DIMENSION."""
    limit = getattr(settings, 'GDRIVE_MAX_DIMENSION', 0)
    if not limit:
        return raw, None
    try:
        from PIL import Image, ImageOps

        with Image.open(io.BytesIO(raw)) as img:
            fmt = img.format
            if fmt not in RESIZABLE or max(img.size) <= limit:
                return raw, None
            img = ImageOps.exif_transpose(img)          # respect phone camera rotation
            img.thumbnail((limit, limit), Image.LANCZOS)
            out = io.BytesIO()
            if fmt == 'JPEG':
                img.convert('RGB').save(out, 'JPEG', quality=90, optimize=True, progressive=True)
            elif fmt == 'WEBP':
                img.save(out, 'WEBP', quality=90)
            else:
                img.save(out, 'PNG', optimize=True)
            return out.getvalue(), RESIZABLE[fmt]
    except Exception:   # not an image Pillow understands (e.g. SVG) — upload as-is
        logger.info('Skipping resize for %s', filename)
        return raw, None


@deconstructible
class GoogleDriveStorage(Storage):

    def __init__(self, folder_id=None, url_template=None):
        self.folder_id = folder_id or settings.GDRIVE_FOLDER_ID
        self.url_template = url_template or settings.GDRIVE_URL_TEMPLATE

    # -- writing -----------------------------------------------------------
    def _save(self, name, content):
        from googleapiclient.http import MediaIoBaseUpload

        filename = os.path.basename(name)
        if hasattr(content, 'seek'):
            content.seek(0)
        raw = content.read()
        data, resized_mime = _downscale(raw, filename)
        mimetype = (
            resized_mime
            or getattr(content, 'content_type', None)
            or mimetypes.guess_type(filename)[0]
            or 'application/octet-stream'
        )

        service = _service()
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mimetype, resumable=True)
        created = service.files().create(
            body={'name': filename, 'parents': [self.folder_id]},
            media_body=media,
            fields='id',
        ).execute()
        file_id = created['id']
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'},
            fields='id',
        ).execute()
        logger.info('Uploaded %s to Google Drive as %s', filename, file_id)

        # ImageField columns hold 100 chars; keep the id intact, trim the filename.
        stored = f'{PREFIX}{file_id}/{filename}'
        return stored[:100]

    def get_available_name(self, name, max_length=None):
        return name   # Drive ids are unique; names never collide

    # -- reading -----------------------------------------------------------
    def url(self, name):
        file_id = _file_id(name)
        if file_id:
            return self.url_template.format(id=file_id)
        # Legacy local path (e.g. demo cards seeded before Drive was enabled)
        return settings.MEDIA_URL + name

    def exists(self, name):
        return False

    def _open(self, name, mode='rb'):
        from googleapiclient.http import MediaIoBaseDownload

        file_id = _file_id(name)
        if not file_id:
            raise FileNotFoundError(name)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, _service().files().get_media(fileId=file_id))
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return ContentFile(buf.getvalue(), name=os.path.basename(name))

    def size(self, name):
        file_id = _file_id(name)
        if not file_id:
            return 0
        meta = _service().files().get(fileId=file_id, fields='size').execute()
        return int(meta.get('size', 0))

    # -- deleting ----------------------------------------------------------
    def delete(self, name):
        file_id = _file_id(name)
        if not file_id:
            return
        try:
            _service().files().delete(fileId=file_id).execute()
            logger.info('Deleted Google Drive file %s', file_id)
        except Exception as exc:   # already gone, or no permission — don't break the request
            logger.warning('Could not delete Drive file %s: %s', file_id, exc)
