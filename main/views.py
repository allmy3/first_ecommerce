import random
import string

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .forms import LoginForm, CheckOutForm, CouponForm, RefundForm
from .models import *


def create_ref_code():
	return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def is_valid_form(values):
	valid = True
	for field in values:
		if field == '':
			valid = False
	return valid


class IndexView(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		products = Product.objects.all()
		context = {
			'products': products,
		}
		return render(request, 'index.html', context)


@login_required
def product_detail(request, product_id):
	product = get_object_or_404(Product, pk=product_id)
	context = {
		'product': product
	}
	# Give add_product or remove_product btn
	if request.user.is_authenticated:
		user = request.user
		order_qs = Order.objects.filter(user=user, ordered=False)
		if order_qs.exists():
			order = order_qs[0]
			if order.products.filter(product__pk=product.pk).exists():
				at_cart = True
			else:
				at_cart = False
		else:
			at_cart = False
		context['at_cart'] = at_cart

	return render(request, 'product_detail.html', context)


class CategoryListView(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		categories = ProductCategory.objects.all()
		context = {
			'categories': categories,
		}
		return render(request, 'categories.html', context)


class LoginPage(View):

	def get(self, request, *args, **kwargs):
		form = LoginForm(request.POST or None)
		return render(request, 'login.html', {'form': form})

	def post(self, request, *args, **kwargs):
		form = LoginForm(request.POST or None)
		if form.is_valid():
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			user = authenticate(username=username, password=password)
			if user:
				login(request, user)
				return redirect('index')
		context = {
			'form': form,
		}
		return render(request, 'login.html', context)


class LogoutPage(View):

	def get(self, request, *args, **kwargs):
		logout(request)
		return redirect('login')


class RegisterPage(View):

	def get(self, request, *args, **kwargs):
		form = UserCreationForm(request.POST or None)
		return render(request, 'register.html', {'form': form})

	def post(self, request, *args, **kwargs):
		form = UserCreationForm(request.POST or None)
		if form.is_valid():
			new_user = form.save(commit=False)
			new_user.save()
			return redirect('login')
		context = {
			'form': form,
		}
		return render(request, 'register.html', context)


@login_required
def add_to_cart(request, product_id):
	product = get_object_or_404(Product, pk=product_id)
	order_product,created = OrderProduct.objects.get_or_create(user=request.user, product=product, order_status=False)
	order_qs = Order.objects.filter(user=request.user, ordered=False)
	if order_qs.exists():
		order = order_qs[0]
		if order.products.filter(product__pk=product.pk).exists():
			order_product.quantity += 1
			order_product.save()
			messages.info(request, "Кол-во товара успешно обновлено!")
			return redirect(request.META.get('HTTP_REFERER'))
		else:
			order.products.add(order_product)
			messages.info(request, "Этот товар был добавлен вам в корзину!")
			return redirect(request.META.get('HTTP_REFERER'))
	else:
		ordered_date = timezone.now()
		order = Order.objects.create(user=request.user, ordered_date=ordered_date)
		order.products.add(order_product)
		messages.info(request, "Этот товар был добавлен вам в корзину!")
		return redirect(request.META.get('HTTP_REFERER'))


@login_required
def remove_from_cart(request, product_id):
	product = get_object_or_404(Product, pk=product_id)
	order_qs = Order.objects.filter(user=request.user, ordered=False)
	if order_qs.exists():
		order = order_qs[0]
		if order.products.filter(product__pk=product.pk).exists():
			order_product = OrderProduct.objects.filter(product=product, user=request.user, order_status=False)[0]
			order.products.remove(order_product)
			order_product.delete()
			messages.info(request, 'Этот продукт был успешно удален из вашей корзины')
			return redirect(request.META.get('HTTP_REFERER'))
		else:
			messages.info(request, "Этого продукта нет у вас в корзине")
			return redirect(request.META.get('HTTP_REFERER'))
	else:
		messages.info(request, "Этого продукта нет у вас в корзине")
		return redirect(request.META.get('HTTP_REFERER'))


@login_required
def remove_product_for_order_sum(request, product_id):
	product = get_object_or_404(Product, pk=product_id)
	order_qs = Order.objects.filter(user=request.user, ordered=False)
	if order_qs.exists():
		order = order_qs[0]
		if order.products.filter(product__pk=product.pk).exists():
			order_product = OrderProduct.objects.filter(user=request.user, product=product, order_status=False)[0]
			if order_product.quantity > 1:
				order_product.quantity -= 1
				order_product.save()
			else:
				order.products.remove(order_product)
			messages.info(request, 'Кол-во этого товара было обновлено')
			return redirect('order_sum')
		else:
			messages.info(request, 'Этого товара нет у вас в корзине')
			return redirect('order_sum')
	else:
		messages.info(request, 'У вас нет активного заказа(корзины)')
		return redirect('product', pk=product.pk)


class CheckOutPage(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		try:
			order = Order.objects.get(user=request.user, ordered=False)
			form = CheckOutForm()
			context = {
				'form': form,
				'order': order, 
				'couponform': CouponForm(),
				'DISPLAY_COUPON_FORM': True,
			}

			shipping_address_qs = Address.objects.filter(
				user=request.user,
				address_type='S',
				default=True,
			)
			if shipping_address_qs.exists():
				context.update({'default_shipping_address': shipping_address_qs[0]})

			billing_address_qs = Address.objects.filter(
				user=request.user,
				address_type='B',
				default=True,
			)
			if billing_address_qs.exists():
				context.upload({'default_billing_address': billing_address_qs[0]})
			return render(request, 'chekout.html', context)
		except ObjectDoesNotExist:
			messages.info(self.request, "У вас нет активного заказа!")
			return redirect('checkout')

	def post(self, request, *args, **kwargs):
		form = CheckOutForm(request.POST or None)
		try:
			order = Order.objects.get(user=request.user, ordered=False)
			if form.is_valid():
				use_default_shipping = form.cleaned_data.get('use_default_shipping')
				if use_default_shipping:
					address_qs = Address.objects.filter(user=request.user, address_type='S', default=True)
					if address_qs.exists():
						shipping_address = address_qs[0]
						order.shipping_address = shipping_address
						order.save()
					else:
						messages.info(request, 'По умолчанию этот адрес не доступен')
						return redirect('checkout')
				else:
					shipping_address1 = form.cleaned_data.get('shipping_address')
					shipping_address2 = form.cleaned_data.get('shipping_address2')
					shipping_country = form.cleaned_data.get('shipping_country')
					shipping_zip = form.cleaned_data.get('shipping_zip')

					if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
						shipping_address = Address(
							user=request.user,
							street_address=shipping_address1,
							apartment_address=shipping_address2,
							country=shipping_country,
							zip=shipping_zip,
							address_type='S'
						)
						shipping_address.save()

						order.sipping_address = shipping_address
						order.save()

						set_default_shipping = form.cleaned_data.get('set_default_shipping')
						if set_default_shipping:
							shipping_address.default = True
							shipping_address.save()
					else:
						messages.info(request, 'Пожалуйста, заполните обязательные поля адреса доставки ')

				use_default_billing = form.cleaned_data.get('use_default_billing')
				same_billing_address = form.cleaned_data.get('same_billing_address')

				if same_billing_address:
					billing_address = shipping_address
					billing_address.pk = None
					billing_address.save()
					billing_address.address_type = 'B'
					billing_address.save()
					order.billing_address = billing_address
					order.save()

				elif use_default_billing:
					address_qs = Address.objects.filter(
						user=request.user,
						address_type='B',
						default=True
					)
					if address_qs.exists():
						billing_address = address_qs[0]
						order.billing_address = billing_address
						order.save()
					else:
						messages.info(request, 'Нет доступных адресов такого типа по умолчанию')
						return redirect('checkout')
				else:
					billing_address1 = form.cleaned_data.get('billing_address')
					billing_address2 = form.cleaned_data.get('billing_address2')
					billing_country = form.cleaned_data.get('billing_country')
					billing_zip = form.cleaned_data.get('billing_zip')

					if is_valid_form([billing_address1, billing_country, billing_zip]):
						billing_address = Address(
							user=request.user,
							street_address=billing_address1,
							apartment_address=billing_address2,
							country=billing_country,
							zip=billing_zip,
							address_type='B'
						)
						billing_address.save()

						order.billing_address = billing_address
						order.save()

						set_default_billing = form.cleaned_data.get('set_default_billing')
						if set_default_billing:
							billing_address.default = True
							billing_address.save()
					else:
						messages.info(request, 'Пожалуйста, заполните обязательные поля платежного адреса ')

				payment_option = form.cleaned_data.get('payment_option')

				if payment_option == 'T':
					return redirect('payment_page', payment_option='Tinkoff_bank')
				elif payment_option == 'Z':
					return redirect('payment_page', payment_option='ZberBank')
				elif payment_option == 'U':
					return redirect('payment_page', payment_option='UMoney')
				else:
					messages.info(request, 'Выбрана недействительная платежная система')
					return redirect('checkout')

		except ObjectDoesNotExist:
			messages.info(request, 'У вас нет активного заказа')
			return redirect('order_sum')


class PaymentPageForExample(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		order = Order.objects.get(user=request.user, ordered=False)
		context = {
			'order': order,
			'DISPLAY_COUPON_FORM': False,
		}
		user_profile = request.user.profile
		if user_profile.one_click_purchasing:
			pass
		return render(request, 'payment.html', context)


class OrderSummaryPage(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		try:
			order = Order.objects.get(user=self.request.user, ordered=False)
			context = {
				'order': order,
			}
			return render(request, 'order_summary.html', context)
		except ObjectDoesNotExist:
			messages.warning(request, "У вас нет возможных заказов")
			return redirect('index')


class FavoritesPage(LoginRequiredMixin, View):

	def get(self, request, *args, **kwargs):
		user_fav = Favorite.objects.filter(user=request.user).first()
		context = {
			'user_fav': user_fav
		}
		return render(request, 'favorites.html', context)


@login_required()
def add_to_fav(request, product_id):
	user = request.user
	product = get_object_or_404(Product, pk=product_id)
	favourites_qs = Favorite.objects.filter(user=user)
	if favourites_qs.exists():
		favorites = favourites_qs[0]
		if favorites.fav_products.filter(pk=product_id).exists():
			favorites.fav_products.remove(product)
			messages.info(request, 'Продукт успешно удален из избранных')
		else:
			favorites.fav_products.add(product)
			messages.info(request, 'Продукт успешно добавлен в избранные')
	else:
		fav = Favorite.objects.create(user=request.user)
		fav.fav_products.add(product)

	return redirect(request.META.get('HTTP_REFERER'))