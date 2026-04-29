from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class CustomPasswordResetForm(PasswordResetForm):
    username = forms.CharField(required=True, label="Tài khoản")

    def clean(self):
        cleaned_data = super().clean()
        username = (cleaned_data.get('username') or '').strip()
        email = (cleaned_data.get('email') or '').strip()

        if not username or not email:
            return cleaned_data

        if not User.objects.filter(username=username, email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("Tài khoản và email không khớp hoặc không tồn tại trong hệ thống.")

        return cleaned_data

    def get_users(self, email):
        username = (self.cleaned_data.get('username') or '').strip()
        active_users = User.objects.filter(
            username=username,
            email__iexact=email,
            is_active=True,
        )
        return (u for u in active_users if u.has_usable_password())


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email này đã tồn tại trong hệ thống.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get('email') or '').strip().lower()
        if commit:
            user.save()
        return user


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
