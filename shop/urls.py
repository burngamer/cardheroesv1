from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('cards/', views.card_list, name='card_list'),
    path('cards/one-piece/', views.card_list, {'franchise': 'OP'}, name='one_piece'),
    path('cards/lorcana/', views.card_list, {'franchise': 'DI'}, name='lorcana'),
    path('card/<slug:slug>/', views.card_detail, name='card_detail'),
    path('card/<slug:slug>/review/', views.review_submit, name='review_submit'),
    path('card/<slug:slug>/review/delete/', views.review_delete, name='review_delete'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:card_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:card_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('faq/', views.faq, name='faq'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/orders/<int:order_id>/status/', views.dashboard_order_status, name='dashboard_order_status'),
    path('dashboard/cards/', views.dashboard_cards, name='dashboard_cards'),
    path('dashboard/cards/add/', views.dashboard_card_edit, name='dashboard_card_add'),
    path('dashboard/cards/<int:pk>/edit/', views.dashboard_card_edit, name='dashboard_card_edit'),
    path('dashboard/cards/<int:pk>/delete/', views.dashboard_card_delete, name='dashboard_card_delete'),
    path('dashboard/users/', views.dashboard_users, name='dashboard_users'),
    path('dashboard/users/add/', views.dashboard_user_add, name='dashboard_user_add'),
    path('dashboard/users/<int:pk>/edit/', views.dashboard_user_edit, name='dashboard_user_edit'),
    path('dashboard/users/<int:pk>/delete/', views.dashboard_user_delete, name='dashboard_user_delete'),
    path('dashboard/users/<int:pk>/reset-password/', views.dashboard_user_reset_password, name='dashboard_user_reset_password'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/orders/', views.order_history, name='order_history'),
]
