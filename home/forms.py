from django import forms
from .models import Post, Comment, Reply,User,UserProfile

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
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match")

        return cleaned_data
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                status="denied"
            )
        return user
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)