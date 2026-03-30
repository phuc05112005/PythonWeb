from django import forms

class MailForm(forms.Form):
    subject = forms.CharField(label="Vấn đề", max_length=255)
    message = forms.CharField(label="Nội dung", widget=forms.Textarea)