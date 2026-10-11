from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Card(models.Model):
    class Franchise(models.TextChoices):
        ONE_PIECE = 'OP', 'One Piece'
        LORCANA = 'DI', 'Lorcana'

    class Rarity(models.TextChoices):
        COMMON = 'C', _('Common')
        UNCOMMON = 'U', _('Uncommon')
        RARE = 'R', _('Rare')
        SUPER_RARE = 'SR', _('Super Rare')
        SECRET_RARE = 'SEC', _('Secret Rare')
        LEGENDARY = 'L', _('Legendary')

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    franchise = models.CharField(max_length=2, choices=Franchise.choices)
    rarity = models.CharField(max_length=3, choices=Rarity.choices, default=Rarity.COMMON)
    card_set = models.CharField(max_length=120, blank=True, help_text='Set / collection the card belongs to')
    card_number = models.CharField(max_length=30, blank=True)
    condition = models.CharField(max_length=60, default='Near Mint')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='cards/', blank=True, null=True)
    back_image = models.ImageField(upload_to='cards/backs/', blank=True, null=True, help_text='The back side of the card')
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_franchise_display()})'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f'{self.name}-{self.card_number}' if self.card_number else self.name)
            slug = base
            n = 2
            while Card.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:card_detail', args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0


class Review(models.Model):
    RATING_CHOICES = [(i, f'{i} star{"s" if i > 1 else ""}') for i in range(1, 6)]

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['card', 'user'], name='one_review_per_user_per_card'),
        ]

    def __str__(self):
        return f'{self.user} — {self.card} ({self.rating}★)'


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'P', _('Pending')
        PAID = 'PA', _('Paid')
        SHIPPED = 'S', _('Shipped')
        CANCELLED = 'X', _('Cancelled')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='orders',
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.PAID)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk}'

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    card = models.ForeignKey(Card, on_delete=models.SET_NULL, null=True)
    card_name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity} x {self.card_name}'

    @property
    def subtotal(self):
        return self.price * self.quantity
