from decimal import Decimal

from django.conf import settings

from .models import Card


class Cart:
    """Session-based shopping cart."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def save(self):
        self.session.modified = True

    def add(self, card, quantity=1, override=False):
        cid = str(card.pk)
        if cid not in self.cart:
            self.cart[cid] = {'quantity': 0, 'price': str(card.price)}
        if override:
            self.cart[cid]['quantity'] = quantity
        else:
            self.cart[cid]['quantity'] += quantity
        self.cart[cid]['quantity'] = max(1, min(self.cart[cid]['quantity'], card.stock))
        self.save()

    def remove(self, card):
        cid = str(card.pk)
        if cid in self.cart:
            del self.cart[cid]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        cards = Card.objects.filter(pk__in=self.cart.keys())
        cart = self.cart.copy()
        for card in cards:
            item = cart[str(card.pk)]
            item = {
                'card': card,
                'quantity': item['quantity'],
                'price': Decimal(item['price']),
            }
            item['subtotal'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    @property
    def total(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )
