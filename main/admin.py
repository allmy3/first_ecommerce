from django.contrib import admin
from .models import *


admin.site.register(ProductCategory)
admin.site.register(ForProductCategory)
admin.site.register(ImageProductContent)
admin.site.register(Product)
admin.site.register(OrderProduct)
admin.site.register(Order)
admin.site.register(Address)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(Favorite)
admin.site.register(UserProfile)