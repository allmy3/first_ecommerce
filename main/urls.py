from django.urls import path

from .views import *

urlpatterns = [
	path('', IndexView.as_view(), name='index'),
	path('category-list/', CategoryListView.as_view(), name='category_list'),
	path('product-detail-<int:product_id>/', product_detail, name='product'),
	path('login/', LoginPage.as_view(), name='login'),
	path('register/', RegisterPage.as_view(), name='register'),
	path('logout/', LogoutPage.as_view(), name='logout'),
	path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
	path('remove-from-cart/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
	path('remove-single/<int:product_id>/', remove_product_for_order_sum, name='remove_single'),
	path('cart/order-sum/', OrderSummaryPage.as_view(), name='order_sum'),
	path('cart/checkout/', CheckOutPage.as_view(), name='checkout'),
	path('cart/payment-procedure/<payment_option>/', PaymentPageForExample.as_view(), name='payment_page'),
	path('favorites/add/<int:product_id>/', add_to_fav, name='add_to_fav'),
	path('favorites/', FavoritesPage.as_view(), name='fav'),
]