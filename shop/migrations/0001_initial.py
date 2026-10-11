from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(blank=True, max_length=140, unique=True)),
                ('franchise', models.CharField(choices=[('OP', 'One Piece'), ('DI', 'Disney')], max_length=2)),
                ('rarity', models.CharField(choices=[('C', 'Common'), ('U', 'Uncommon'), ('R', 'Rare'), ('SR', 'Super Rare'), ('SEC', 'Secret Rare'), ('L', 'Legendary')], default='C', max_length=3)),
                ('card_set', models.CharField(blank=True, help_text='Set / collection the card belongs to', max_length=120)),
                ('card_number', models.CharField(blank=True, max_length=30)),
                ('condition', models.CharField(default='Near Mint', max_length=60)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('stock', models.PositiveIntegerField(default=1)),
                ('image', models.ImageField(blank=True, null=True, upload_to='cards/')),
                ('featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=120)),
                ('email', models.EmailField(max_length=254)),
                ('address', models.CharField(max_length=250)),
                ('city', models.CharField(max_length=100)),
                ('postal_code', models.CharField(max_length=20)),
                ('country', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('P', 'Pending'), ('PA', 'Paid'), ('S', 'Shipped'), ('X', 'Cancelled')], default='PA', max_length=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_name', models.CharField(max_length=120)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('card', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.card')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='shop.order')),
            ],
        ),
    ]
