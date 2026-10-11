from django.contrib import admin

from .models import Card, Order, OrderItem, Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['card', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['card__name', 'user__username', 'comment']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['name', 'franchise', 'rarity', 'price', 'stock', 'featured', 'has_back']

    @admin.display(boolean=True, description='Back image')
    def has_back(self, obj):
        return bool(obj.back_image)
    list_filter = ['franchise', 'rarity', 'featured']
    list_editable = ['price', 'stock', 'featured']
    search_fields = ['name', 'card_set', 'description']
    prepopulated_fields = {'slug': ('name',)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['card']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]
