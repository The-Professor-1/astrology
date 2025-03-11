from django.urls import path,include
from .views import home, like_post,delete_post, add_comment, add_reply, user_register, user_login, user_logout,delete_comment ,delete_reply

urlpatterns = [
    path("", home, name="home"),
    path("register/", user_register, name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("like/<int:post_id>/", like_post, name="like_post"),
    path("comment/<int:post_id>/", add_comment, name="add_comment"),
    path("reply/<int:comment_id>/", add_reply, name="add_reply"),
    path('delete_comment/<int:comment_id>/', delete_comment, name='delete_comment'),
    path('delete_reply/<int:reply_id>/', delete_reply, name='delete_reply'),
    path('delete_post/<int:post_id>/', delete_post, name='delete_post'),
]