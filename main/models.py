from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.models import Sum
from django.urls import reverse

from django_countries.fields import CountryField


TYPE_PRODUCT_LABELS = (
	('P', 'primary'),
	('S', 'secondary'),
	('D', 'danger'),
)

ADDRESS_CHOICES = (
	('B', 'billing'),
	('S', 'shipping'),
)


class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='profile')
	stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
	one_click_purchasing = models.BooleanField(default=False)

	def __str__(self):
		return self.user.username


class ProductCategory(models.Model):
	name = models.CharField(max_length=255, verbose_name='Название категории')
	slug = models.SlugField(max_length=255, verbose_name='URL для категории')

	def __str__(self):
		return self.name

	class Meta:
		verbose_name = 'Категория (продукта)'
		verbose_name_plural = 'Категории (продуктов)'


class ForProductCategory(models.Model):
	name = models.CharField(max_length=255, verbose_name='Название под-категории')
	slug = models.SlugField(max_length=255, verbose_name='URL для под-категории')
	category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, verbose_name='Категория для под-категории', related_name="pod")

	def __str__(self):
		return self.name

	class Meta:
		verbose_name = 'Под-категория'
		verbose_name_plural = 'Под-категории'


class ImageProductContent(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
	image = models.ImageField(upload_to='product_images/', verbose_name='Фото')

	class Meta:
		verbose_name = 'Фото контент продукта'
		verbose_name_plural = 'Фото контент продуктов'


class Product(models.Model):
	title = models.CharField(max_length=150, verbose_name='Название продукта')
	poster = models.ImageField(upload_to='product_posters/', verbose_name='Постер продукта', blank=True, null=True)
	price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена товара')
	discount_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Начальная цена товара')
	category = models.ForeignKey(ForProductCategory, on_delete=models.CASCADE, verbose_name='Категория товара')
	product_type_label = models.CharField(max_length=1, choices=TYPE_PRODUCT_LABELS, verbose_name='Тип редкости')
	slug = models.SlugField(max_length=150, verbose_name='URL для продукта')
	description = models.TextField("Описание товара")
	image_content = models.ManyToManyField(ImageProductContent, blank=True, verbose_name='Фотки продукта')
	product_qt = models.PositiveSmallIntegerField(default=1, verbose_name='Кол-во товара в наличии')

	def __str__(self):
		return self.title

	class Meta:
		verbose_name = 'Продукт'
		verbose_name_plural = 'Продукты'
		ordering = ['-pk']


class OrderProduct(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
	order_status = models.BooleanField(default=False)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Продукт')
	quantity = models.PositiveSmallIntegerField(default=1, verbose_name='Кол-во продукта для заказа')

	def __str__(self):
		return self.user.username + " " + self.product.title

	def get_total_price(self):
		return self.quantity * self.product.price

	def get_total_discount_price(self):
		return self.quantity * self.product.discount_price

	def get_summ_of_saved_money(self):
		return self.get_total_price() - self.get_total_discount_price()

	def get_price(self):
		if self.product.discount_price:
			return self.get_total_discount_price()
		return self.get_total_price()

	class Meta:
		verbose_name = 'Продукт для заказа'
		verbose_name_plural = 'Продукты для заказов'


class Order(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='orders')
	ref_code = models.CharField(max_length=20, blank=True, null=True)
	products = models.ManyToManyField(OrderProduct)
	start_date = models.DateTimeField(auto_now_add=True)
	ordered_date = models.DateTimeField()
	ordered = models.BooleanField(default=False)
	shipping_address = models.ForeignKey('Address', on_delete=models.SET_NULL, verbose_name="Адрес доставки", related_name='shipping_address', blank=True, null=True)
	billing_address = models.ForeignKey('Address', on_delete=models.SET_NULL, verbose_name="Адрес для выставления счета", related_name='billing_address', blank=True, null=True)
	payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, verbose_name='Платеж', blank=True, null=True)
	coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, verbose_name='Купон', blank=True, null=True)
	being_delivered = models.BooleanField(default=False, verbose_name='Достовляется')
	recieved = models.BooleanField(default=False, verbose_name='Получен')
	refund_requested = models.BooleanField(default=False, verbose_name='Запрошен возврат')
	refund_granted = models.BooleanField(default=False, verbose_name='Возврат гарантирован')

	def __str__(self):
		return self.user.username

	def get_total(self):
		total_price = 0
		for order_product in self.products.all():
			total_price += int(order_product.get_total_price())
		if self.coupon:
			total_price -= int(self.coupon.amount)
		return total_price

	class Meta:
		verbose_name = 'Заказ'
		verbose_name_plural = 'Заказы'


class Address(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
	street_address = models.CharField(max_length=100, verbose_name='Адрес улицы')
	apartment_address = models.CharField(max_length=100, verbose_name='Адрес здания')
	county = CountryField(multiple=False)
	zip = models.CharField(max_length=100)
	address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
	default = models.BooleanField(default=False)

	def __str__(self):
		return self.user.username

	class Meta:
		verbose_name = 'Адрес'
		verbose_name_plural = 'Адреса'


class Payment(models.Model):
	stripe_charge_id = models.CharField(max_length=50)
	user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='Пользователь', blank=True, null=True)
	amount = models.FloatField()
	timestamp = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.user.username

	class Meta:
		verbose_name = 'Платеж'
		verbose_name_plural = 'Платежи'


class Coupon(models.Model):
	code = models.CharField(max_length=15)
	amount = models.FloatField()

	def __str__(self):
		return self.code

	class Meta:
		verbose_name = 'Купон'
		verbose_name_plural = 'Купоны'


class Refund(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ')
	reason_for = models.TextField()
	accepted = models.BooleanField(default=False)
	email = models.EmailField()

	def __str__(self):
		return str(self.pk)

	class Meta:
		verbose_name = 'Запрос на возврат'
		verbose_name_plural = 'Запросы на возврат'


class Favorite(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
	fav_products = models.ManyToManyField(Product, blank=True, verbose_name='Продукты')

	def __str__(self):
		return self.user.username

	class Meta:
		verbose_name = 'Избранное'
		verbose_name_plural = 'Избранные'


def userprofile_receiver(sender, instance, created, *args, **kwargs):
	if created:
		userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=User)
