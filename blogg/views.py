from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


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
