from django import forms


class PurchaseForm(forms.Form):
    category_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, initial=1)
    phone_number = forms.CharField(max_length=32, help_text='Mobile money phone number')


class ReserveTicketsForm(forms.Form):
    category_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.HiddenInput)
    payment_method = forms.ChoiceField(
        choices=[('mobile_money', 'Mobile Money'), ('airtel_money', 'Airtel Money')],
        initial='mobile_money',
        label='Payment method',
    )
    email_address = forms.EmailField(label='Email address', required=True)
    phone_number = forms.CharField(max_length=32, label='Phone number', required=True)
