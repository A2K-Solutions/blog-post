import os
from random import randint
from django.db import IntegrityError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib.auth import get_user_model


# Create your views here.
@login_required(login_url='user-login')
def home(request):
    """
    This is a function for home page it is rendering index.html file. We have written a ORM to filter and show only published posts on home page.Creating a form: It creates an instance of the BlogForm form, passing the request object as an argument. This is done to handle form submissions and display the form in the template.
    By including form in the context dictionary and passing it to the index.html template, the form will be accessible in the template and can be rendered to allow users to create new blog posts.
    :param request: (HttpRequest): The HTTP request object representing the incoming request from the user.
    :return:
            HttpResponse: The rendered 'index.html' template with the context containing the published blog posts and the form.
    """
    published_posts = BlogPost.objects.filter(status='published')
    form = BlogForm(request=request)
    context = {'blog_posts': published_posts, 'form': form}
    return render(request, 'index.html', context)


def random_digits(digits_len=4):
    """
        Generate a random integer with the specified number of digits.

        This function generates a random integer with the specified number of digits. By default, it generates a 4-digit random
        integer. The range of possible random integers is determined based on the number of digits specified. The generated
        integer is inclusive of the lower range start and exclusive of the upper range end.

        Parameters:
            digits_len (int): The number of digits in the generated random integer. Default is 4.

        Returns:
            int: A random integer with the specified number of digits.
        """
    range_start = 10 ** (digits_len - 1)
    range_end = (10 ** digits_len) - 1
    return randint(range_start, range_end)


def verification_code(request, email=None):
    """
        Process the verification code form and validate the entered code.

        This function handles the verification code form submission. If the form is submitted via POST and is valid, it retrieves
        the entered verification code and the corresponding user's email address. It checks if the verification code matches the
        one stored in the user's profile. If the code matches, a new random verification code is generated and saved in the user's
        profile, and the user is redirected to the reset password page. If the code does not match or there is no user with the
        provided email address, an error message is displayed.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.
            email (str, optional): The email address associated with the user. Defaults to None.

        Returns:
            HttpResponse: A redirect response to the reset password page if the verification code is valid. Otherwise, renders
                          the 'verification_code' template with the verification code form.

        """
    if request.method == "POST":
        codeform = CodeForm(request.POST or None)
        if codeform.is_valid():
            try:
                user = User.objects.get(email=email)
                user_profile = UserProfile.objects.get(user=user)
                verification_code = user_profile.verification_code
                code = request.POST.get('code')
                if verification_code == code:
                    user_profile.verification_code = random_digits()
                    user_profile.save()
                    return redirect('reset-password', email)
            except User.DoesNotExist:
                messages.error(request, "There is no user with this Email ID.")
    form = CodeForm()
    context = {'form': form}
    return render(request, 'verification_code.html', context)


User = get_user_model()


def user_register(request):
    """Handle user registration.
    If the user is already authenticated, they will be redirected to the home page.
    Otherwise, a registration form is displayed for the user to fill out.
    When a POST request is received with valid form data, a new user account is created and saved.
    A success message is displayed, and the user is redirected to the login page.

    :param request: (HttpRequest): The HTTP request object representing the incoming request from the user.
    :return:
    HttpResponse: The rendered 'user_register.html' template with the context containing the form.
    """
    if request.user.is_authenticated:
        return redirect('home')
    else:
        form = UserRegisterForm()
        if request.method == "POST":
            form = UserRegisterForm(request.POST)
            if form.is_valid():
                user = form.save()
                full_name = user.get_full_name()

                verification_code = random_digits()
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    user_profile.verification_code = verification_code
                    user_profile.save()
                except UserProfile.DoesNotExist:
                    user_profile = UserProfile.objects.create(user=user, verification_code=verification_code)
                except IntegrityError as e:
                    user.delete()
                    messages.error(request, "An error occurred during registration. Please try again.")
                    return redirect('user-register')

                messages.success(request, f"Account successfully created for {full_name}")
                return redirect('user-login')

        context = {'form': form}
        return render(request, 'user_register.html', context)


@csrf_exempt
def user_login(request):
    """Handle user login.
        If the user is already authenticated, they will be redirected to the home page.
        Otherwise, a login form is displayed for the user to fill out.
        When a POST request is received with valid form data, user will be wuthenticated and if user is present
        in database and all the info given correct they will be logged in and redirected to homepage.
        If username or password given are not correct an error message is shown.

        :param request: (HttpRequest): The HTTP request object representing the incoming request from the user.
        :return:
        HttpResponse: The rendered 'user_login.html' template with the context containing the form.
        """
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Username or password is incorrect')

        context = {}
        return render(request, 'user_login.html', context)


def signout(request):
    """
        Log out the currently authenticated user.
        This function logs out the user by calling the `logout` function provided by Django's authentication system.
        After logging out, the user is redirected to the login page.
        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.

        Returns:
            HttpResponse: A redirect response to the login page.
        """
    logout(request)
    return redirect('user-login')


@login_required(login_url='user-login')
def create_blog(request):
    """
        Create a new blog post.
        This function handles the creation of a new blog post. If the user is not authenticated, they will be redirected
        to the login page specified by the 'user-login' URL.
        When a POST request is received, the function processes the submitted form data. If the form contains the 'save_draft'
        field, the blog post is saved as a draft. Otherwise, if the form is valid, the blog post is published and saved.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.

        Returns:
            HttpResponse: A redirect response to the 'my-blogs' page if the post is saved as a draft,
                          or a redirect response to the 'blog-detail' page for the published blog post.

        """
    if request.method == 'POST':
        form = BlogForm(request.POST, request=request)
        if 'save_draft' in request.POST:
            form.save(draft=True)  # Save as draft
            return redirect('my-blogs')
        elif form.is_valid():
            blog_post = form.save(draft=False)  # Publish the blog post
            return redirect('blog-detail', slug=blog_post.slug)
    else:
        form = BlogForm(request=request)

    context = {'form': form}
    return render(request, 'blog_form.html', context)


def blog_detail(request, slug):
    """
        Display the detail view of a blog post.
        This function retrieves the blog post with the specified slug from the database or returns a 404 error if not found.
        It also retrieves the comments associated with the blog post and initializes an empty comment form.
        If a POST request is received, the function delegates the comment creation process to the `create_comment` function.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.
            slug (str): The slug of the blog post.

        Returns:
            HttpResponse: The rendered 'blog_detail.html' template with the blog post, comments, and comment form.
        """
    blog_post = get_object_or_404(BlogPost, slug=slug)
    comments = blog_post.comments.all()
    form = CommentForm()

    if request.method == 'POST':
        return create_comment(request, slug)

    context = {
        'blog_post': blog_post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog_detail.html', context)


def my_blogs(request):
    """
        Display the user's blog posts on the "My Blogs" page.
        This function retrieves the blog posts authored by the currently authenticated user from the database.
        It filters the blog posts into two categories: draft posts and published posts.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.

        Returns:
            HttpResponse: The rendered 'my_blogs.html' template with the draft posts and published posts.
        """
    blog_posts = BlogPost.objects.filter(author=request.user)
    draft_posts = blog_posts.filter(status='draft')
    published_posts = blog_posts.filter(status='published')

    context = {'draft_posts': draft_posts, 'published_posts': published_posts}
    return render(request, 'my_blogs.html', context)


def publish_blog(request, slug):
    """
        Publish a draft blog post.
        This function retrieves the draft blog post with the specified slug, authored by the currently authenticated user,
        from the database. It updates the status of the blog post to 'published' and saves the changes.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.
            slug (str): The slug of the blog post.

        Returns:
            HttpResponse: A redirect response to the 'my-blogs' page after publishing the blog post.
        """
    blog_post = get_object_or_404(BlogPost, slug=slug, author=request.user)
    blog_post.status = 'published'
    blog_post.save()
    return redirect('my-blogs')


@login_required(login_url='user-login')
def edit_blog(request, slug):
    """
        Edit an existing blog post.
        This function retrieves the blog post with the specified slug, authored by the currently authenticated user,
        from the database. It allows the user to modify the blog post by rendering the 'blog_form.html' template.
        If a POST request is received, the function validates the submitted form data. If the 'save_draft' button is clicked,
        the blog post is saved as a draft. Otherwise, if the form is valid, the blog post is updated and saved.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.
            slug (str): The slug of the blog post to be edited.

        Returns:
            HttpResponse: The rendered 'blog_form.html' template with the form to edit the blog post.
        """
    blog_post = get_object_or_404(BlogPost, slug=slug, author=request.user)
    if request.method == 'POST':
        form = BlogForm(request.POST, instance=blog_post, request=request)
        if 'save_draft' in request.POST:  # Check if save_draft button is clicked
            form.save(draft=True)  # Save as draft
            return redirect('my-blogs')
        elif form.is_valid():
            blog_post = form.save()  # Publish the blog post
            return redirect('blog-detail', slug=blog_post.slug)
    else:
        form = BlogForm(instance=blog_post, request=request)

    context = {'form': form, 'blog_post': blog_post}
    return render(request, 'blog_form.html', context)


@login_required(login_url='user-login')
def delete_blog(request, slug):
    """
        Delete a blog post.
        This function retrieves the blog post with the specified slug, authored by the currently authenticated user,
        from the database. If a POST request is received, indicating confirmation for deletion, the blog post is deleted
        from the database. The function then redirects the user to the 'my-blogs' page.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.
            slug (str): The slug of the blog post to be deleted.

        Returns:
            HttpResponse: A redirect response to the 'my-blogs' page after deleting the blog post.
        """
    blog_post = get_object_or_404(BlogPost, slug=slug, author=request.user)

    if request.method == 'POST':
        blog_post.delete()
        return redirect('my-blogs')

    context = {
        'blog_posts': BlogPost.objects.filter(author=request.user)
    }
    return render(request, 'my_blogs.html', context)


def create_comment(request, slug):
    """
        Create a new comment on a blog post.
        This function retrieves the blog post with the specified slug from the database. If a POST request is received,
        indicating the submission of a comment form, the function validates the form data, creates a new comment object,
        associates it with the blog post and the authenticated user, and saves it to the database. The function then
        redirects the user to the 'blog-detail' page for the specified blog post. If a GET request is received, the function
        renders the 'blog_detail' template with an empty comment form.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.
            slug (str): The slug of the blog post to which the comment is being created.

        Returns:
            HttpResponse: A redirect response to the 'blog-detail' page for the specified blog post if a comment is
                          successfully created, or a render response to the 'blog_detail' template with an empty comment
                          form if no comment is submitted.
        """
    blog_post = get_object_or_404(BlogPost, slug=slug)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog_post = blog_post
            comment.author = request.user
            comment.save()
            return redirect('blog-detail', slug=slug)

    else:
        form = CommentForm()

    context = {
        'blog_post': blog_post,
        'form': form,
    }
    return render(request, 'blog_detail.html', context)


def search_blogs(request):
    """
        Search for blog posts based on a query string.
        This function retrieves the query string from the GET parameters of the request. It performs a search in the database
        for blog posts whose titles or authors' usernames contain the query string, and are marked as 'published'. The search
        is case-insensitive and partial matches are considered. The search results are stored in the 'results' list. The
        function then renders the 'searched_blogs' template with the query string and the search results.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.

        Returns:
            HttpResponse: A render response to the 'searched_blogs' template with the search query and the search results.
        """
    query = request.GET.get('search_query', '')
    results = []

    if query:
        results = BlogPost.objects.filter(
            models.Q(title__icontains=query) | models.Q(author__username__icontains=query),
            status='published'
        )

    context = {
        'search_query': query,
        'results': results
    }

    return render(request, 'searched_blogs.html', context)


def email(request):
    """
        Process the email form and send the verification code.

        This function handles the email form submission. If the form is submitted via POST and is valid, it retrieves the entered
        email address and attempts to find a user associated with that email address. If a user is found, it retrieves the
        verification code from the user's profile and sends an email to the provided email address with the verification code.
        The user is then redirected to a verification code page. If no user is found with the provided email address, an error
        message is displayed.

        Parameters:
            request (HttpRequest): The HTTP request object representing the incoming request from the user.

        Returns:
            HttpResponse: A redirect response to the verification code page if the form submission is successful. Otherwise,
                          renders the 'email_form' template with the email form.

        """
    if request.method == "POST":
        emailform = EmailForm(request.POST or None)
        if emailform.is_valid():
            email = request.POST.get('email')
            user_email = User.objects.filter(email=email).last()
            user_profile = UserProfile.objects.get(user=user_email)
            verification_code = user_profile.verification_code
            if user_email is not None:
                context = f"""
                            Your verification code to change password is {verification_code}"""
                send_mail(
                    'Contact Form Received!',
                    context,
                    'tm825141@gmail.com',
                    [email],
                    fail_silently=False,
                )
                return redirect('verification-code', email)
            else:
                messages.error(request, "There is no user with this Email ID.")
    form = EmailForm()
    context = {
        'form': form
    }
    return render(request, 'email_form.html', context)


def reset_password(request, email=None):
    if request.method == "POST":
        password_form = ResetPasswordForm(request.POST or None)
        if password_form.is_valid():
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                return redirect('user-login')
            else:
                messages.error(request, "Passwords are not same.")

    form = ResetPasswordForm()
    context = {
        'form': form
    }
    return render(request, 'forgot_password.html', context)


@login_required(login_url='user-login')
def change_password(request):
    if request.method == "POST":
        user = request.user
        current_password = request.user.password
        changeform = ChangePasswordForm(request.POST or None)

        if changeform.is_valid():
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            matcheck = check_password(old_password, current_password)

            if matcheck:
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    return redirect('home')

    form = ChangePasswordForm()
    context = {
        'form': form
    }
    return render(request, 'change_password.html', context)


def user_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            # Remove the existing profile picture
            if form.cleaned_data['profile_picture'] and form.cleaned_data['profile_picture'].name != 'default.jpg':
                default_picture_path = os.path.join(settings.MEDIA_ROOT, 'profile_pics', 'default.jpg')
                if os.path.exists(default_picture_path):
                    os.remove(default_picture_path)

            form.save()
            return redirect('user-profile')
    else:
        form = UserProfileForm(instance=request.user.userprofile)
    return render(request, 'user_profile.html', {'form': form})
