from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from .utils import generate_token
from .models import User
from django.conf import settings
from .forms import SignupForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import LoginForm

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until email is confirmed
            user.save()

            # Send email verification
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('authapp/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': generate_token.make_token(user),
            })
            # user.email_user(mail_subject, message)
            email = EmailMessage(subject=mail_subject, body=message,
                         from_email=settings.EMAIL_FROM_USER,
                         to=[user.email]
                         )
            email.send()

            return render(request, 'authapp/email_verification_sent.html')
    else:
        form = SignupForm()
    return render(request, 'authapp/signup.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, 'Account is not active. Please verify your email.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'authapp/login.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_bytes(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and generate_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'authapp/account_confirmed.html')
    else:
        return render(request, 'authapp/account_confirmation_invalid.html')
