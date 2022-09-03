from django.conf import settings
from django.core.validators import validate_email
from django.contrib.auth.hashers import make_password
from authentication.models import CustomUser
import msal
import requests
import string
import random


ms_settings = settings.MICROSOFT #imports credentials dictionary from settings.py
graph_url = 'https://graph.microsoft.com/v1.0' #This is a call to graph API v1.0


def get_user(token):
    r = requests.get(
        url='{0}/me'.format(graph_url),
        headers={'Authorization': 'Bearer {0}'.format(token)},
    )
    return r.json()


def load_cache(request):
    cache = msal.SerializableTokenCache()
    if request.session.get('token_cache'):
        cache.deserialize(request.session['token_cache'])
    return cache


def save_cache(request, cache):
    if cache.has_state_changed:
        request.session['token_cache'] = cache.serialize()


def get_msal_app(cache=None):
    # Initialize the MSAL confidentials from Azure client registration
    auth_app = msal.ConfidentialClientApplication(
        ms_settings['app_id'],
        authority=ms_settings['authority'],
        client_credential=ms_settings['app_secret'],
        token_cache=cache
    )
    return auth_app



def get_sign_in_flow(redirect):

    auth_app = get_msal_app()
    return auth_app.initiate_auth_code_flow(
        ms_settings['scopes'],
        redirect_uri=redirect,
    )



def get_token_from_code(request):
    cache = load_cache(request)
    auth_app = get_msal_app(cache)
    flow = request.session.pop('auth_flow', {})
    result = auth_app.acquire_token_by_auth_code_flow(flow, request.GET)
    save_cache(request, cache)
    return result


def get_token(request):
    cache = load_cache(request)
    auth_app = get_msal_app(cache)

    accounts = auth_app.get_accounts()
    if accounts:
        result = auth_app.acquire_token_silent(#silent renewal of expired tokens
            ms_settings['scopes'],
            account=accounts[0]
        )
        save_cache(request, cache)
        return result['access_token']


def remove_user_and_token(request):
    if 'token_cache' in request.session:
        del request.session['token_cache']

    if 'user' in request.session:
        del request.session['user']

# https://{authority}/oauth2/v2.0/logout?post_logout_redirect_uri=http://localhost:8000/logout
# revise logout url to match the hostname but not a priority since the site has a custo domain
def get_logout_url():
    return (ms_settings["authority"] + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + ms_settings["logout_uri"]
            )


 # fUNCTION added by Dr. Mburu to validate received email using email validators
def validate_username(username):
    try:
        validate_email(username)
        email = username
    except validate_email.ValidationError:
        pass
    return email


def get_django_user(email,firstname,surname):
    if not validate_username(username=email):
        return
    try:
        user = CustomUser.objects.get(email=email) #check if email exists
        if user is not None: # If exists, update the email and status flags
            user.username=email
            user.is_active=True
            user.is_staff=True
            user.save()
    except CustomUser.DoesNotExist: # If does not exist, try creating a new record
        random_password = ''.join(random.choice(string.ascii_letters) for i in range(32))
        if firstname or surname is None:
            try:
                firstname=email.split("@")[0].capitalize()
                surname=email.split("@")[0].capitalize()
                user = CustomUser(username=email,email=email,first_name=firstname,
                        last_name=surname,password=make_password(random_password))
                user.is_active = True
                user.is_staff = True
                user.save()

            except IntegrityError:
                pass #Ignore creating new user in the database if it exists
    return user # this gave me hard time but now returns user to auth_decorators
