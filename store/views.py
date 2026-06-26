from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import ContactForm, CustomPasswordResetForm, CustomSetPasswordForm, LoginForm, NewsletterForm, ProfileForm, RegistrationForm, SearchForm
from .models import Brand, Category, Contact, HomepageBanner, Product, Review, Testimonial, Wishlist


LANDING_CONTEXT = {
    'categories': Category.objects.filter(is_featured=True)[:6],
    'featured_products': Product.objects.filter(featured=True, is_active=True).select_related('category', 'brand')[:8],
    'trending_products': Product.objects.filter(trending=True, is_active=True).select_related('category', 'brand')[:8],
    'testimonials': Testimonial.objects.filter(is_active=True)[:6],
    'banners': HomepageBanner.objects.filter(is_active=True)[:3],
}


def landing_context():
    return {
        'categories': Category.objects.filter(is_featured=True)[:6],
        'featured_products': Product.objects.filter(featured=True, is_active=True).select_related('category', 'brand')[:8],
        'trending_products': Product.objects.filter(trending=True, is_active=True).select_related('category', 'brand')[:8],
        'testimonials': Testimonial.objects.filter(is_active=True)[:6],
        'banners': HomepageBanner.objects.filter(is_active=True)[:3],
        'why_choose_us': [
            'Premium Quality',
            'Fast Delivery',
            'Original Products',
            'Modern Fashion',
            'Trusted Brand',
            'Affordable Luxury',
        ],
    }


def home(request):
    context = landing_context()
    context.update({'contact_form': ContactForm(), 'newsletter_form': NewsletterForm()})
    return render(request, 'landing/home.html', context)


@login_required
def dashboard(request):
    context = {
        'latest_products': Product.objects.filter(is_active=True).select_related('category', 'brand')[:4],
        'recommended_categories': Category.objects.all()[:6],
        'wishlist_count': Wishlist.objects.filter(user=request.user).count(),
        'product_count': Product.objects.filter(is_active=True).count(),
        'recent_reviews': Review.objects.filter(user=request.user).select_related('product')[:5],
    }
    return render(request, 'dashboard/dashboard.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:dashboard')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, 'Your account has been created.')
        return redirect('store:dashboard')
    return render(request, 'authentication/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:shop')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        if not form.cleaned_data.get('remember_me'):
            request.session.set_expiry(0)
        messages.success(request, 'Welcome back.')
        return redirect('store:shop')
    return render(request, 'authentication/login.html', {'form': form})


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('store:home')


@login_required
def shop(request):
    form = SearchForm(request.GET or None)
    products = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('reviews')

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    brand_slug = request.GET.get('brand', '').strip()
    sort = request.GET.get('sort', '').strip()

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(brand__name__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'popular':
        products = products.annotate(review_count=Count('reviews')).order_by('-review_count', '-created')
    else:
        products = products.order_by('-created')

    context = {
        'form': form,
        'products': products,
        'categories': Category.objects.all(),
        'brands': Brand.objects.all(),
    }
    return render(request, 'shop/shop.html', context)


@login_required
def categories(request):
    return render(request, 'shop/categories.html', {'categories': Category.objects.all()})


@login_required
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_active=True).select_related('brand')
    return render(request, 'shop/category_detail.html', {'category': category, 'products': products})


@login_required
def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images', 'reviews__user'),
        slug=slug,
        is_active=True,
    )
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    wishlist_exists = Wishlist.objects.filter(user=request.user, product=product).exists()
    return render(
        request,
        'shop/product_detail.html',
        {
            'product': product,
            'related_products': related_products,
            'wishlist_exists': wishlist_exists,
        },
    )


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product', 'product__category', 'product__brand')
    return render(request, 'shop/wishlist.html', {'items': items})


@login_required
def wishlist_toggle(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.info(request, 'Removed from wishlist.')
    else:
        messages.success(request, 'Added to wishlist.')
    return redirect('store:product-detail', slug=slug)


@login_required
def profile_view(request):
    profile = request.user.profile
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('store:profile')
    return render(request, 'profile/profile.html', {'form': form, 'profile': profile})


def contact_create(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Thank you for contacting us.')
        return redirect('store:home')
    context = landing_context()
    context.update({'contact_form': form, 'newsletter_form': NewsletterForm()})
    return render(request, 'landing/home.html', context)


def newsletter_create(request):
    form = NewsletterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Subscribed successfully.')
        return redirect('store:home')
    context = landing_context()
    context.update({'newsletter_form': form, 'contact_form': ContactForm()})
    return render(request, 'landing/home.html', context)


@login_required
def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        products = Product.objects.filter(is_active=True).filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(brand__name__icontains=query)
        ).select_related('category', 'brand')[:8]
        for product in products:
            results.append(
                {
                    'name': product.name,
                    'slug': product.slug,
                    'category': product.category.name,
                    'price': str(product.discounted_price),
                    'url': product.get_absolute_url(),
                }
            )
    return JsonResponse({'results': results})


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'authentication/password_change_form.html'
    success_url = reverse_lazy('store:password_change_done')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'authentication/password_reset_form.html'
    email_template_name = 'authentication/password_reset_email.html'
    success_url = reverse_lazy('store:password_reset_done')
    form_class = CustomPasswordResetForm


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'authentication/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'authentication/password_reset_confirm.html'
    success_url = reverse_lazy('store:password_reset_complete')
    form_class = CustomSetPasswordForm


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'authentication/password_reset_complete.html'
