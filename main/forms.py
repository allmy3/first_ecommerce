from django import forms
from django.contrib.auth.models import User

from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from .models import *

PAYMENT_CHOICES = (
	('T', 'Tinkoff_bank'),
	('Z', 'Zberbank'),
	('U', 'UMoney'),
)


class LoginForm(forms.ModelForm):

	password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}))
	username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Логин'}))

	class Meta:
		model = User
		fields = ['username', 'password']

	def clean(self):
		username = self.cleaned_data['username']
		password = self.cleaned_data['password']
		user = User.objects.filter(username=username).first()
		if not user:
			raise forms.ValidationError(f"Пользователь с логином {username} не найден в системе!")
		if not user.check_password(password):
			raise forms.ValidationError('Неверный пароль')
		return self.cleaned_data


class CheckOutForm(forms.Form):

	shipping_address = forms.CharField(required=False)
	shipping_address2 = forms.CharField(required=False)
	shipping_country = CountryField(blank_label="(select your country)").formfield(required=False,widget=CountrySelectWidget(attrs={"class": "custom-select d-block w-100"}))
	shipping_zip = forms.CharField(required=False)

	billing_address = forms.CharField(required=False)
	billing_address2 = forms.CharField(required=False)
	billing_country = CountryField(blank_label="(выберите вашу страну)").formfield(required=False,widget=CountrySelectWidget(attrs={"class": "custom-select d-block w-100"}))
	billing_zip = forms.CharField(required=False)

	same_billing_address = forms.BooleanField(required=False)
	set_default_shipping = forms.BooleanField(required=False)
	use_default_shipping = forms.BooleanField(required=False)
	set_default_billing = forms.BooleanField(required=False)
	use_default_billing = forms.BooleanField(required=False)

	payment_option = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):

	code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Промо-код','aria-label': 'Recipient\'s username','aria-describedby': 'basic-addon2'}))


class RefundForm(forms.Form):

	ref_code = forms.CharField()
	message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
	email = forms.EmailField()
