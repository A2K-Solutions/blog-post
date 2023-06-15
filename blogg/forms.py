from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm
from ckeditor.widgets import CKEditorWidget


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


class BlogForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(config_name='default'))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = BlogPost
        fields = ['title', 'short_description', 'content']

    def save(self, draft=False, commit=True, *args, **kwargs):
        instance = super().save(commit=False)
        instance.author = self.request.user
        instance.slug = slugify(instance.title)

        if draft:
            instance.status = 'draft'
        else:
            instance.status = 'published'

        if commit:
            instance.save()
        return instance


class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={'rows': 4, 'placeholder': 'Your comment', 'class': 'form-control', 'style': 'background: #fff;'}
        )
    )

    class Meta:
        model = Comment
        fields = ['content']


class SearchForm(forms.Form):
    search_query = forms.CharField(label='Search', max_length=100)


class EmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']


class CodeForm(forms.Form):
    code = forms.IntegerField(help_text="Enter 4 digit verification code")


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(max_length=100, required=True)
    confirm_password = forms.CharField(max_length=100, required=True)


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(max_length=100, required=True)
    new_password = forms.CharField(max_length=100, required=True)
    confirm_password = forms.CharField(max_length=100, required=True)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']
