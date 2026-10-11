"""Create the Card Heroes admin account from environment variables.

    DJANGO_SUPERUSER_USERNAME   (required)
    DJANGO_SUPERUSER_PASSWORD   (required)
    DJANGO_SUPERUSER_EMAIL      (optional)

If the account already exists it is left untouched (so a password you changed
on the site is not overwritten on the next deploy). Use --reset-password to
force the password back to the env value, e.g. if you get locked out.

The password is never printed.
"""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create the admin account from DJANGO_SUPERUSER_* environment variables.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-password', action='store_true',
                            help='Reset an existing account\'s password to DJANGO_SUPERUSER_PASSWORD.')

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
        if not username or not password:
            raise CommandError('Set DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD first.')

        User = get_user_model()
        user = User.objects.filter(username=username).first()

        if user and not options['reset_password']:
            changed = False
            if not (user.is_staff and user.is_superuser):
                user.is_staff = user.is_superuser = True
                changed = True
            if changed:
                user.save(update_fields=['is_staff', 'is_superuser'])
            self.stdout.write(f'Admin "{username}" already exists — left unchanged.')
            return

        candidate = user or User(username=username, email=email)
        try:
            validate_password(password, user=candidate)
        except ValidationError as exc:
            raise CommandError('DJANGO_SUPERUSER_PASSWORD is too weak: ' + ' '.join(exc.messages))

        if user:
            user.set_password(password)
            user.is_staff = user.is_superuser = True
            if email:
                user.email = email
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Admin "{username}": password reset from environment.'))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Admin "{username}" created.'))
