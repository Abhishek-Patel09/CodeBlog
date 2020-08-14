from django.shortcuts import render,redirect,get_object_or_404, reverse, get_list_or_404, Http404
from django.core.mail import mail_admins
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth.decorators import login_required
import datetime
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.http import HttpResponse
from django.contrib import messages
from .models import Language, Snippet, Tag
from django.db.models import Q
from .forms import SnippetForm, ContactForm, LoginForm, CreateUserForm, SettingForm, SearchForm
from .utils import paginate_result
from .decorators import private_snippet

# Create your views here.
def index(request):
    if request.method == 'POST':
        f = SnippetForm(request, request.POST)

        if f.is_valid():
            snippet = f.save(request)
            return redirect(reverse('codeblog:snippet_detail', args=[snippet.slug]))

    else :
        f = SnippetForm(request)
        return render(request, 'codeblog/index.html', {'form' : f})


@private_snippet
def snippet_detail(request, snippet_slug):
    snippet = get_object_or_404(Snippet, slug=snippet_slug)
    snippet.hits +=1
    snippet.save()
    return render(request, 'codeblog/snippet_detail.html', {'snippet' : snippet})


@private_snippet
def download_snippet(request, snippet_slug):
    snippet = get_object_or_404(Snippet, slug=snippet_slug)
    file_extension = snippet.language.file_extension
    filename = snippet.slug + file_extension
    res = HttpResponse(snippet.original_code)
    res['content-disposition'] = 'attachment ; filename = ' + filename + ";"
    return res


@private_snippet
def raw_snippet(request, snippet_slug):
    snippet = get_object_or_404(Snippet, slug=snippet_slug)
    return HttpResponse(snippet.original_code, content_type=snippet.language.mime)


def trending_snippets(request, language_slug=''):
    lang = None
    snippets = Snippet.objects
    if language_slug:
        snippets = snippets.filter(language__slug= language_slug)
        lang = get_object_or_404(Language, slug = language_slug)

    snippet_list = get_list_or_404(snippets.filter(exposure='public').order_by('-hits'))
    snippets = paginate_result(request, snippet_list, 5)

    return render(request, 'codeblog/trending.html', {'snippets': snippets, 'lang': lang})


def contact(request):
    if request.method == 'POST':
        f = ContactForm(request, request.POST)      #__initial__ is updated in forms.py therefore we have to pass here two parameters
        if f.is_valid():

            if request.user.is_authenticated:
                name = request.user.username
                email = request.user.email

            else:
                name = f.cleaned_data['name']
                email = f.cleaned_data['email']

            subject = "You have a new Feedback from {}:<{}>".format(name, f.cleaned_data['email'])

            message = "Purpose: {}\n\nDate: {}\n\nMessage:\n\n {}".format(
                dict(f.purpose_choices).get(f.cleaned_data['purpose']),
                datetime.datetime.now(),
                f.cleaned_data['message']
            )

            mail_admins(subject, message)
            messages.add_message(request, messages.INFO, 'Thanks for submitting your feedback.')

            return redirect('codeblog:contact')

    else :
        f = ContactForm(request)

    return render(request, 'codeblog/contact.html', {'form': f})


def tag_list(request, tag):
    t = get_object_or_404(Tag, name=tag)
    snippet_list = get_list_or_404(t.snippet_set)
    snippets = paginate_result(request, snippet_list, 5)
    return render(request, 'codeblog/tag_list.html', {'snippets': snippets, 'tag': t})

def login(request):
    if request.user.is_authenticated:
        return redirect('codeblog:profile', username=request.user.username)

    if request.method == 'POST':

        f = LoginForm(request.POST)

        if f.is_valid():
            user = User.objects.filter(email=f.cleaned_data['email'])

            if user:
                user = auth.authenticate(
                    username = user[0].username,
                    password = f.cleaned_data['password'],
                )

                if user:
                    auth.login(request, user)
                    return redirect(request.GET.get('next') or 'codeblog:index')

            messages.add_message( request, messages.INFO, 'Invalid email/password.')
            return redirect('codeblog:login')

    else:
        f = LoginForm()

    return render(request, 'codeblog/login.html', {'form': f})


@login_required
def logout(request):
    auth.logout(request)
    return render(request, 'codeblog/logout.html')

@login_required
def user_details(request):
    user = get_object_or_404(User, id=request.user.id)
    return render(request, 'codeblog/user_details.html', {'user':user})



def profile(request, username):
    return HttpResponse("<p>Profile page of #{}</p>".format(username))


def signup(request):
    if request.method == 'POST':
        f = CreateUserForm(request.POST)
        if f.is_valid():
            f.save(request)
            messages.success(request, 'Account created successfully. Check email to verify the account.')
            return redirect('codeblog:signup')

    else :
        f = CreateUserForm()

    return render(request, 'codeblog/signup.html', {'form': f})

def activate_account(request, uid64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uid64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if(user is not None and default_token_generator.check_token(user, token)):
        user.is_active = True
        user.save()
        messages.add_message(request, messages.INFO, 'Account activated. Please login.')
    else:
        messages.add_message(request, message.INFO, 'Link Expired.')

    return redirect('codeblog:login')


@login_required
def settings(request):
    user = get_object_or_404(User, id=request.user.id)
    if request.method == 'POST':
        f = SettingsForm(request.POST, instance=user.profile)       #instance to pre-populate or our form with the values corresponding to username
        if f.is_valid():
            f.save()
            messages.add_message(request, messages.INFO, 'Settings Saved.')
            return redirect(reverse('codeblog:settings'))

    else :
        f = SettingForm(instance=user.profile)

    return render(request, 'codeblog/settings.html', {'form': f})


def profile(request, username):
    user = get_object_or_404(User, username=username)

    #if the profile is private and logged in user is not same as the user being viewed,
    #show 404 error
    if user.profile.private and request.user.username != user.username :
        raise Http404

    #if the profile is not private and logged in user is not same as the user being viewed,
    #then show public snippets of the user
    elif not user.profile.private and request.user.username != user.username :
        snippet_list = user.snippet_set.filter(exposure='public')
        user.profile.views +=1
        user.profile.save()

    #logged in user is same as the user being viewed
    #show everything
    else:
        snippet_list = user.snippet_set.all()

    snippets = paginate_result(request, snippet_list, 5)

    return render(request, 'codeblog/profile.html',
                    {'user': user, 'snippets': snippets })


@login_required
def delete_snippet(request, snippet_slug):
    snippet = get_object_or_404(Snippet, slug=snippet_slug)
    if not snippet.user == request.user:
        raise Http404
    snippet.delete()
    return redirect('codeblog:profile', request.user)


def search(request):
    f = SearchForm(request.GET)
    snippets = []

    if f.is_valid():

        query = f.cleaned_data.get('query')
        mysnippets = f.cleaned_data.get('mysnippet')

        # if mysnippet field is selected, search only logged in user's snippets
        if mysnippets:
            snippet_list = Snippet.objects.filter( Q(user=request.user), Q(original_code__icontains=query) | Q(title__icontains=query))

        else :
            qs1 = Snippet.objects.filter( Q(exposure='public'), Q(original_code__icontains=query) | Q(title__icontains=query))

            # to search in users own private snippet
            if request.user.is_authenticated :
                qs2 = Snippet.objects.filter(Q(user=request.user), Q(original_code__icontains=query) | Q(title__icontains=query))
                snippet_list = (qs1 | qs2).distinct()

            else :
                snippet_list = qs1

        snippets = paginate_result(request, snippet_list, 5)

    return render(request, 'codeblog/search.html', {'form': f, 'snippets': snippets})
