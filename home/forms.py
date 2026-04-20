from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Kiểm tra xem email có tồn tại và thuộc về một user đang hoạt động không
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("Email này không tồn tại trong hệ thống. Vui lòng kiểm tra lại!")
        return email

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