from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg, Count, DecimalField, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from .cart import Cart
from .forms import (
    CardForm, CartAddForm, CheckoutForm, ProfileForm, RegisterForm,
    UserCreateForm, UserEditForm,
)
from .models import Card, Order, OrderItem, Review


def rated(qs):
    """Annotate a Card queryset with review stats."""
    return qs.annotate(avg_rating=Avg('reviews__rating'), num_reviews=Count('reviews', distinct=True))


def home(request):
    featured = rated(Card.objects.filter(featured=True, stock__gt=0))[:8]
    latest = rated(Card.objects.filter(stock__gt=0))[:8]
    return render(request, 'shop/home.html', {'featured': featured, 'latest': latest})


SORT_OPTIONS = [
    ('new', gettext_lazy('Newest first')),
    ('price_asc', gettext_lazy('Price: low to high')),
    ('price_desc', gettext_lazy('Price: high to low')),
    ('rating', gettext_lazy('Best rated')),
    ('name', gettext_lazy('Name A–Z')),
]


def card_list(request, franchise=None):
    base = Card.objects.all()
    title = _('All Cards')
    if franchise:
        base = base.filter(franchise=franchise)
        title = dict(Card.Franchise.choices).get(franchise, _('Cards'))
    cards = rated(base)

    query = request.GET.get('q', '').strip()
    if query:
        cards = cards.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(card_set__icontains=query))

    rarity = request.GET.get('rarity', '')
    if rarity:
        cards = cards.filter(rarity=rarity)

    card_set = request.GET.get('set', '')
    if card_set:
        cards = cards.filter(card_set=card_set)

    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    try:
        if min_price:
            cards = cards.filter(price__gte=float(min_price.replace(',', '.')))
        if max_price:
            cards = cards.filter(price__lte=float(max_price.replace(',', '.')))
    except ValueError:
        pass

    in_stock = request.GET.get('stock') == '1'
    if in_stock:
        cards = cards.filter(stock__gt=0)

    sort = request.GET.get('sort', 'new')
    if sort == 'price_asc':
        cards = cards.order_by('price')
    elif sort == 'price_desc':
        cards = cards.order_by('-price')
    elif sort == 'rating':
        cards = cards.order_by(F('avg_rating').desc(nulls_last=True), '-num_reviews')
    elif sort == 'name':
        cards = cards.order_by('name')
    else:
        sort = 'new'

    sets = base.exclude(card_set='').values_list('card_set', flat=True).distinct().order_by('card_set')

    return render(request, 'shop/card_list.html', {
        'cards': cards,
        'title': title,
        'query': query,
        'rarity': rarity,
        'rarities': Card.Rarity.choices,
        'franchise': franchise,
        'card_set': card_set,
        'sets': sets,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock,
        'sort': sort,
        'sort_options': SORT_OPTIONS,
    })


def card_detail(request, slug):
    card = get_object_or_404(rated(Card.objects.all()), slug=slug)
    form = CartAddForm()
    related = rated(Card.objects.filter(franchise=card.franchise).exclude(pk=card.pk))[:4]
    reviews = card.reviews.select_related('user')
    my_review = None
    if request.user.is_authenticated:
        my_review = reviews.filter(user=request.user).first()
    return render(request, 'shop/card_detail.html', {
        'card': card, 'form': form, 'related': related,
        'reviews': reviews, 'my_review': my_review,
    })


@login_required
@require_POST
def review_submit(request, slug):
    card = get_object_or_404(Card, slug=slug)
    try:
        rating = int(request.POST.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0
    if not 1 <= rating <= 5:
        messages.error(request, _('Pick a star rating between 1 and 5.'))
        return redirect(card.get_absolute_url())
    comment = request.POST.get('comment', '').strip()[:2000]
    _review, created = Review.objects.update_or_create(
        card=card, user=request.user,
        defaults={'rating': rating, 'comment': comment},
    )
    messages.success(request, _('Review posted. Thanks, nakama!') if created else _('Your review has been updated.'))
    return redirect(card.get_absolute_url())


@login_required
@require_POST
def review_delete(request, slug):
    card = get_object_or_404(Card, slug=slug)
    Review.objects.filter(card=card, user=request.user).delete()
    messages.success(request, _('Your review has been removed.'))
    return redirect(card.get_absolute_url())


@require_POST
def cart_add(request, card_id):
    cart = Cart(request)
    card = get_object_or_404(Card, pk=card_id)
    if card.stock < 1:
        messages.error(request, _('"%(name)s" is sold out.') % {'name': card.name})
        return redirect(card.get_absolute_url())
    form = CartAddForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(card, quantity=cd['quantity'], override=cd['override'])
        messages.success(request, _('"%(name)s" added to your cart.') % {'name': card.name})
    return redirect('shop:cart_detail')


@require_POST
def cart_remove(request, card_id):
    cart = Cart(request)
    card = get_object_or_404(Card, pk=card_id)
    cart.remove(card)
    return redirect('shop:cart_detail')


def cart_detail(request):
    return render(request, 'shop/cart.html')


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.info(request, _('Your cart is empty.'))
        return redirect('shop:card_list')
    initial = {}
    if request.user.is_authenticated:
        initial = {'full_name': request.user.get_full_name(), 'email': request.user.email}
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            items = list(cart)
            with transaction.atomic():
                # Lock the cards and re-check stock so two buyers can't buy the last copy
                locked = {c.pk: c for c in Card.objects.select_for_update().filter(pk__in=[i['card'].pk for i in items])}
                short = [i['card'].name for i in items
                         if i['card'].pk not in locked or locked[i['card'].pk].stock < i['quantity']]
                if short:
                    messages.error(request, _('Not enough stock left for: %(cards)s. Please update your cart.')
                                   % {'cards': ', '.join(short)})
                    return redirect('shop:cart_detail')
                order = form.save(commit=False)
                if request.user.is_authenticated:
                    order.user = request.user
                order.save()
                for item in items:
                    card = locked[item['card'].pk]
                    OrderItem.objects.create(
                        order=order,
                        card=card,
                        card_name=card.name,
                        price=card.price,          # always the current price, never a stale one
                        quantity=item['quantity'],
                    )
                    card.stock -= item['quantity']
                    card.save(update_fields=['stock'])
            cart.clear()
            return render(request, 'shop/order_success.html', {'order': order})
    else:
        form = CheckoutForm(initial=initial)
    return render(request, 'shop/checkout.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Welcome aboard, %(name)s!') % {'name': user.username})
            return redirect('shop:home')
    else:
        form = RegisterForm()
    return render(request, 'shop/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile has been updated.'))
            return redirect('shop:profile')
    else:
        form = ProfileForm(instance=request.user)
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    total_spent = sum(order.total for order in orders)
    cards_owned = sum(item.quantity for order in orders for item in order.items.all())
    return render(request, 'shop/profile.html', {
        'form': form,
        'orders': orders[:5],
        'order_count': orders.count(),
        'total_spent': total_spent,
        'cards_owned': cards_owned,
    })


def faq(request):
    return render(request, 'shop/faq.html')


REVENUE_EXPR = Sum(F('price') * F('quantity'), output_field=DecimalField())


@staff_member_required
def dashboard(request):
    revenue = OrderItem.objects.filter(order__status__in=['PA', 'S']).aggregate(t=REVENUE_EXPR)['t'] or 0
    status_counts = {row['status']: row['n'] for row in Order.objects.values('status').annotate(n=Count('id'))}
    recent_orders = Order.objects.prefetch_related('items').order_by('-created_at')[:8]
    top_sellers = (
        OrderItem.objects.values('card_name')
        .annotate(sold=Sum('quantity'), revenue=REVENUE_EXPR)
        .order_by('-sold')[:5]
    )
    low_stock = Card.objects.filter(stock__lte=2).order_by('stock', 'name')[:8]
    return render(request, 'shop/dashboard.html', {
        'revenue': revenue,
        'order_count': Order.objects.count(),
        'pending_count': status_counts.get('P', 0) + status_counts.get('PA', 0),
        'shipped_count': status_counts.get('S', 0),
        'card_count': Card.objects.count(),
        'stock_total': Card.objects.aggregate(t=Sum('stock'))['t'] or 0,
        'sold_out_count': Card.objects.filter(stock=0).count(),
        'recent_orders': recent_orders,
        'top_sellers': top_sellers,
        'low_stock': low_stock,
        'statuses': Order.Status.choices,
        'storage_warning': not settings.DEBUG and not settings.USE_GDRIVE,
    })


@staff_member_required
@require_POST
def dashboard_order_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    status = request.POST.get('status')
    if status in dict(Order.Status.choices):
        order.status = status
        order.save()
        messages.success(request, _('Order #%(id)s marked as %(status)s.')
                         % {'id': order.pk, 'status': order.get_status_display()})
    return redirect('shop:dashboard')


@staff_member_required
def dashboard_cards(request):
    cards = Card.objects.all().order_by('name')
    query = request.GET.get('q', '').strip()
    if query:
        cards = cards.filter(Q(name__icontains=query) | Q(card_set__icontains=query) | Q(card_number__icontains=query))
    return render(request, 'shop/dashboard_cards.html', {'cards': cards, 'query': query})


@staff_member_required
def dashboard_card_edit(request, pk=None):
    card = get_object_or_404(Card, pk=pk) if pk else None
    if request.method == 'POST':
        form = CardForm(request.POST, request.FILES, instance=card)
        if form.is_valid():
            saved = form.save()
            if card:
                messages.success(request, _('"%(name)s" updated.') % {'name': saved.name})
            else:
                messages.success(request, _('"%(name)s" added to the vault.') % {'name': saved.name})
            return redirect('shop:dashboard_cards')
    else:
        form = CardForm(instance=card)
    return render(request, 'shop/dashboard_card_form.html', {
        'form': form,
        'card': card,
        'storage_warning': not settings.DEBUG and not settings.USE_GDRIVE,
    })


@staff_member_required
@require_POST
def dashboard_card_delete(request, pk):
    card = get_object_or_404(Card, pk=pk)
    name = card.name
    card.delete()
    messages.success(request, _('"%(name)s" removed from the vault.') % {'name': name})
    return redirect('shop:dashboard_cards')


def _can_touch_user(request, target):
    """Guard rails for user management."""
    if target.pk == request.user.pk:
        return False, _("You can't modify or delete your own account from here — use your profile.")
    if target.is_superuser and not request.user.is_superuser:
        return False, _('Only a superuser can manage another superuser.')
    return True, ''


@staff_member_required
def dashboard_users(request):
    users = User.objects.annotate(n_orders=Count('orders')).order_by('-is_superuser', '-is_staff', 'username')
    query = request.GET.get('q', '').strip()
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    return render(request, 'shop/dashboard_users.html', {'users': users, 'query': query})


@staff_member_required
def dashboard_user_add(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['role'] == 'superuser' and not request.user.is_superuser:
                messages.error(request, _('Only a superuser can create superusers.'))
            else:
                user = form.save()
                messages.success(request, _('Account "%(name)s" created.') % {'name': user.username})
                return redirect('shop:dashboard_users')
    else:
        form = UserCreateForm()
    return render(request, 'shop/dashboard_user_form.html', {'form': form, 'target': None})


@staff_member_required
def dashboard_user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)
    allowed, reason = _can_touch_user(request, target)
    if not allowed:
        messages.error(request, reason)
        return redirect('shop:dashboard_users')
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=target)
        if form.is_valid():
            if form.cleaned_data['is_superuser'] and not request.user.is_superuser:
                messages.error(request, _('Only a superuser can grant superuser privileges.'))
            else:
                form.save()
                messages.success(request, _('Account "%(name)s" updated.') % {'name': target.username})
                return redirect('shop:dashboard_users')
    else:
        form = UserEditForm(instance=target)
    orders = Order.objects.filter(user=target)[:5]
    return render(request, 'shop/dashboard_user_form.html', {'form': form, 'target': target, 'orders': orders})


@staff_member_required
@require_POST
def dashboard_user_reset_password(request, pk):
    target = get_object_or_404(User, pk=pk)
    if target.is_superuser and not request.user.is_superuser:
        messages.error(request, _('Only a superuser can manage another superuser.'))
        return redirect('shop:dashboard_users')
    if not target.email:
        messages.error(request, _('"%(name)s" has no email address on file — add one first.') % {'name': target.username})
        return redirect('shop:dashboard_user_edit', pk=pk)
    form = PasswordResetForm({'email': target.email})
    if form.is_valid():
        form.save(request=request, use_https=request.is_secure())
        messages.success(request, _('Password reset link sent to %(email)s.') % {'email': target.email})
    else:
        messages.error(request, _('Could not send the reset email.'))
    return redirect('shop:dashboard_user_edit', pk=pk)


@staff_member_required
@require_POST
def dashboard_user_delete(request, pk):
    target = get_object_or_404(User, pk=pk)
    allowed, reason = _can_touch_user(request, target)
    if not allowed:
        messages.error(request, reason)
    else:
        name = target.username
        target.delete()
        messages.success(request, _('Account "%(name)s" deleted. Their orders are kept for the records.') % {'name': name})
    return redirect('shop:dashboard_users')


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'shop/order_history.html', {'orders': orders})
