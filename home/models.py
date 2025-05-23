from django.db import models # type:ignore
from django.contrib.auth.models import User # type:ignore


# Create your models here.
class SiteStats(models.Model):
    home_page_visits = models.PositiveIntegerField(default=0)
    kokeb_calculator_visits = models.PositiveIntegerField(default=0)
    calculators_list_visits = models.PositiveIntegerField(default=0)
class TransactionNumber(models.Model):
    transaction_number = models.CharField(max_length=100)
class UserProfile(models.Model):
    # One-to-one link to the default User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Status field with choices and default value
    status = models.CharField(
        max_length=10,
        default='denied'
    )
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def like_count(self):
        return self.likes.count()

    def __str__(self):
        return f"Post by {self.user.username} at {self.created_at}"

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="static/")

    def __str__(self):
        return f"Image for Post {self.post.id}"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on Post {self.post.id}"

class Reply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="replies")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="replies")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.user.username} on Comment {self.comment.id}"