from django import forms
from .models import Post, Comment, Reply,User,UserProfile
from django.core.exceptions import ValidationError


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["text"]

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ["text"]
class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_username(self):
        username = self.cleaned_data['username'].lower()  # Convert to lowercase
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")  # Specific message
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username'].lower()  # Ensure lowercase
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")