from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def build_unique_slug(instance, value, slug_field='slug'):
	base_slug = slugify(value) or 'item'
	slug = base_slug
	model = instance.__class__
	counter = 1
	while model.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
		slug = f'{base_slug}-{counter}'
		counter += 1
	return slug


class TimeStampedModel(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class CustomUser(AbstractUser):
	email = models.EmailField(unique=True)

	def __str__(self):
		return self.get_username()


class Category(TimeStampedModel):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True, blank=True)
	description = models.TextField(blank=True)
	image = models.ImageField(
		upload_to='categories/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
	)
	is_featured = models.BooleanField(default=False)

	class Meta:
		ordering = ['name']

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = build_unique_slug(self, self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('store:category-detail', kwargs={'slug': self.slug})


class Brand(TimeStampedModel):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True, blank=True)
	logo = models.ImageField(
		upload_to='brands/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
	)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ['name']

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = build_unique_slug(self, self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class Product(TimeStampedModel):
	category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
	brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, related_name='products', blank=True, null=True)
	name = models.CharField(max_length=180)
	slug = models.SlugField(max_length=220, unique=True, blank=True)
	description = models.TextField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	discount = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
	stock = models.PositiveIntegerField(default=0)
	main_image = models.ImageField(
		upload_to='products/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
	)
	material = models.CharField(max_length=120, blank=True)
	available_sizes = models.JSONField(default=list, blank=True)
	available_colors = models.JSONField(default=list, blank=True)
	specifications = models.JSONField(default=dict, blank=True)
	featured = models.BooleanField(default=False)
	trending = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['-created']

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = build_unique_slug(self, self.name)
		super().save(*args, **kwargs)

	@property
	def discounted_price(self):
		if self.discount:
			return self.price - (self.price * (self.discount / Decimal('100.00')))
		return self.price

	@property
	def in_stock(self):
		return self.stock > 0

	def get_absolute_url(self):
		return reverse('store:product-detail', kwargs={'slug': self.slug})

	def __str__(self):
		return self.name


class ProductImage(TimeStampedModel):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
	image = models.ImageField(
		upload_to='products/gallery/',
		validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
	)
	alt_text = models.CharField(max_length=180, blank=True)

	def __str__(self):
		return f'{self.product.name} image'


class Review(TimeStampedModel):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews')
	rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
	comment = models.TextField()
	is_approved = models.BooleanField(default=True)

	class Meta:
		ordering = ['-created']

	def __str__(self):
		return f'{self.product.name} review by {self.user.username}'


class Wishlist(TimeStampedModel):
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wishlist_items')
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_entries')

	class Meta:
		constraints = [models.UniqueConstraint(fields=['user', 'product'], name='unique_user_wishlist_product')]

	def __str__(self):
		return f'{self.user.username} saved {self.product.name}'


class Contact(TimeStampedModel):
	name = models.CharField(max_length=120)
	email = models.EmailField()
	phone = models.CharField(max_length=30, blank=True)
	message = models.TextField()
	is_read = models.BooleanField(default=False)

	class Meta:
		ordering = ['-created']

	def __str__(self):
		return f'Contact from {self.name}'


class Newsletter(TimeStampedModel):
	email = models.EmailField(unique=True)

	def __str__(self):
		return self.email


class UserProfile(TimeStampedModel):
	GENDER_CHOICES = [
		('male', 'Male'),
		('female', 'Female'),
		('other', 'Other'),
		('prefer_not_to_say', 'Prefer not to say'),
	]

	user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
	phone = models.CharField(max_length=30, blank=True)
	address = models.CharField(max_length=255, blank=True)
	bio = models.TextField(blank=True)
	gender = models.CharField(max_length=25, choices=GENDER_CHOICES, blank=True)
	dob = models.DateField(blank=True, null=True)
	photo = models.ImageField(
		upload_to='profiles/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
	)

	def __str__(self):
		return f'{self.user.username} profile'


class Testimonial(TimeStampedModel):
	name = models.CharField(max_length=120)
	role = models.CharField(max_length=120, blank=True)
	quote = models.TextField()
	rating = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)])
	image = models.ImageField(
		upload_to='testimonials/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
	)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class HomepageBanner(TimeStampedModel):
	title = models.CharField(max_length=180)
	subtitle = models.CharField(max_length=255, blank=True)
	image = models.ImageField(
		upload_to='banners/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
	)
	link_label = models.CharField(max_length=80, blank=True)
	link_url = models.CharField(max_length=255, blank=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['-created']

	def __str__(self):
		return self.title
