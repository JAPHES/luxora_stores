from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('shop/', views.shop, name='shop'),
    path('categories/', views.categories, name='categories'),
    path('shop/category/<slug:slug>/', views.category_detail, name='category-detail'),
    path('shop/product/<slug:slug>/', views.product_detail, name='product-detail'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<slug:slug>/', views.wishlist_toggle, name='wishlist-toggle'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('search/suggestions/', views.search_suggestions, name='search-suggestions'),
    path('contact/', views.contact_create, name='contact'),
    path('newsletter/', views.newsletter_create, name='newsletter'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='authentication/password_change_done.html'), name='password_change_done'),
]