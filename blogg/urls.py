from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('register/', views.user_register, name="user-register"),
    path('login/', views.user_login, name="user-login"),
    path('logout/', views.signout, name="logout_user"),
    path('blog/', views.create_blog, name="create-blog"),
    path('blog/<slug:slug>/', views.blog_detail, name="blog-detail"),
    path('my_blog/', views.my_blogs, name="my-blogs"),
    path('edit_blog/<slug:slug>/', views.edit_blog, name="edit-blog"),
    path('delete_blog/<slug:slug>/', views.delete_blog, name="delete-blog"),
    path('blog/<slug:slug>/create_comment/', views.create_comment, name="create-comment"),
    path('publish/<slug:slug>/', views.publish_blog, name="publish-blog"),
    path('search/', views.search_blogs, name="search"),
    path('verification_code/<str:email>/', views.verification_code, name="verification-code"),
    path('reset_password/<str:email>/', views.reset_password, name="reset-password"),
    path('email_form/', views.email, name="email-form"),
    path('change_password/', views.change_password, name="change-password"),
    path('user_profile/', views.user_profile, name="user-profile"),

]
