from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

class MailForm(forms.Form):
    subject = forms.CharField(
        label="Vấn đề",
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nhập vấn đề bạn gặp phải...',
            'class': 'form-control'
        })
    )

    email = forms.EmailField(
        label="Email của bạn",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Nhập email để shop phản hồi...',
            'class': 'form-control'
        })
    )

    message = forms.CharField(
        label="Nội dung",
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Nhập nội dung chi tiết...',
            'class': 'form-control'
        })
    )