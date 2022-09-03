from django.shortcuts import render, redirect
from django import forms
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login, update_session_auth_hash,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.db.models import Count
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail import send_mail

from .forms import CompleteProfileForm, RegisterForm, ProfileEdit, NewRegister, SignupForm
from .token import account_activation_token
from applications.events_news.models import Event, Attendees
from applications.alumniprofile.models import Profile, Constants, Batch
from applications.news.models import News
from applications.gallery.models import Album
from applications.geolocation.views import addPoints
import datetime
from django.utils import timezone
from itertools import chain
from AlumniConnect.decorators import custom_login_required

# Create your views here.

class LoginFormView(SuccessMessageMixin, LoginView):
    template_name = 'AlumniConnect/login.html'
    redirect_authenticated_user = True
    # success_url = '/'
    success_message = "Logged in successfully!"

def my_login(request):
    """
     Login user only if user is also verified by admin
    """
    # checking if user is already logged in
    if request.user and request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request,data = request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            user = User.objects.get(username = username)
            
            # if user is admin no need to check other thing
            if user.is_staff:
                login(request,user)
                return redirect('home')
            
            
            # checking if user's profile is verified by admin or not
            if user.profile.verify:
                login(request,user)
                return redirect('home')
            else:
                messages.error(request,"Profile either not completed or not verified by admin, can't login")
                return redirect('home')
        else:
            return render(request,'AlumniConnect/login.html',{'form':form})
        
    form = AuthenticationForm()
    return render(request,'AlumniConnect/login.html',{'form':form})


def index(request):
    sname = None
    if request.user.is_authenticated:
        sname = request.user.get_short_name()
    now = timezone.now()
    events = Event.objects.filter(start_date__gte=now).order_by('start_date').annotate(
        count=Count('attendees__user_id'))
    events_completed = Event.objects.filter(end_date__lt=now).order_by('-start_date').annotate(
        count=Count('attendees__user_id'))
    # Add Check here
    news = News.objects.filter().order_by('-date')
    # messages.success(request, 'Your password was successfully updated!')
    events_to_display = list(chain(events, events_completed))[:3]
    albums_list = Album.objects.order_by('-created').annotate(images_count=Count('albumimage'))[:3]
    return render(request, "AlumniConnect/index.html",
                  {'name': sname, 'events': events_to_display, 'news': news, 'albums': albums_list})


def alumniBody(request):
    return render(request, "AlumniConnect/alumnibody.html")


def alumniCard(request):
    return render(request, "AlumniConnect/alumnicard.html")


def gallery(request):
    return render(request, "AlumniConnect/gallery.html")


def job_posting(request):
    return render(request, "AlumniConnect/job_posting.html")


# def jobboard(request):
#     return render(request, "env/Lib/site-packages/gallery.html")



def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            role = request.POST['role']
            roll_no = request.POST['username'] # username and roll_no are same
            
            # user created using form
            user = User.objects.create_user(
                username = form.cleaned_data.get('username'),
                password = form.cleaned_data.get('password'),
                email = form.cleaned_data.get('email'),
                is_active = False
                )
            
            # now making profile for user
            profile = Profile(user=user, roll_no=roll_no, role=role)
            profile.save()
            
             # sending mail for activation
            current_site = get_current_site(request)
            from_email = settings.DEFAULT_FROM_EMAIL
            to = [user.email]
            subject = "[noreply] SAC Account Activation"
            html_message = render_to_string('AlumniConnect/account_activation_email.html', {
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user)
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject = subject,
                message = plain_message,
                from_email = from_email,
                recipient_list=to,
                html_message = html_message,
                fail_silently=False,
            )

            return render(request,"AlumniConnect/confirm_email.html")
        else:
            return render(request, "AlumniConnect/signup.html", {'form': form})

    form = SignupForm()
    return render(request, "AlumniConnect/signup.html", {'form': form})

@custom_login_required
def complete_profile(request):
    
    user = request.user

    try:
        profile = Profile.objects.get(user = user)
    except:
        # admin does not have any profile
        return redirect('home')
    
    try:
        # if profile is already completed then redirect to home
        if profile.verify or profile.reg_no:
            return redirect('home')
    except:
        pass


    #creating context for form
    batches = list(Batch.objects.all().order_by('batch'))
    context = {'edit': False, 'programmes': Constants.PROG_CHOICES,'branches': Constants.BRANCH, 'batches': batches, 'admission_years': Constants.YEAR_OF_ADDMISSION,'user_roll_no':user.username,'user_email':user.email}
    
    
    if request.method == "POST":
        
        # adding reg_no in post data
        reg_no = reg_no_gen(request.POST['programme'], request.POST['branch'], request.POST['year_of_admission'])
       
       
        POST_DATA_COPY = request.POST.copy()
        # POST_DATA_COPY.update({'reg_no':reg_no})   this thing will not work here as reg_no is set as non editable so it can not be edited using modelForm
        form = CompleteProfileForm(POST_DATA_COPY,request.FILES,instance = profile)
        
        if form.is_valid():
            try:
                first_name,last_name = request.POST['name'].split(' ',1)
            except:
                first_name,last_name = request.POST['name'],""
            
            # updating user fields
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            #saving profile
            profile = form.save()
            profile.reg_no = reg_no #setting registeration number 
            profile.save()
            
            
            # now this profile will be on admins portal,
            # we are making user logout, as once admin approve this profile this user will become active and will be able to login.
            logout(request)
            return render(request,'AlumniConnect/profile_completion.html')
        
        else:
            # this case will be handled when complete_profile and editprofile will be merged
            return HttpResponse('Form have errors.')
    else:
        form = CompleteProfileForm()
        return render(request,"AlumniConnect/profileedit.html",context = context)
                        


def register(request):
    check = False
    l = None
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        print(request.POST)
        if form.is_valid():
            batch = form.cleaned_data.get('batch')
            branch = form.cleaned_data.get('branch')
            programme = form.cleaned_data.get('programme')
            l = Profile.objects.filter(batch=batch, programme=programme, branch=branch)
            print('Testing output\n')
            print(l)
            check = True

    else:
        form = RegisterForm()
    return render(request, 'AlumniConnect/registration.html', {'form': form, 'check': check, 'l': l})


def reg_no_gen(degree_, spec_, year):
    degree = {"B.Tech": "1", "B.Des": '2', "M.Tech": '3', "M.Des": '4', "PhD": '5'}
    spec = {"NA": '00', "CSE": "01", "ECE": "02", "ME": "03", "MT": "04", "NS": "05", "DS": "06","SM": "07"}
    last_reg_no = Profile.objects.filter(year_of_admission=year).order_by('user__date_joined').last()
    # print(last_reg_no)
    new_reg_no = (int(str(last_reg_no.reg_no)[-4:]) + 1) if last_reg_no else 1
    return degree[degree_] + spec[spec_] + str(year)[2:] + str(convert_int(new_reg_no, 4))


def convert_int(number, decimals):
    return str(number).zfill(decimals)

"""
    This function needs to be depricated in new signup workflow.
"""
def new_register(request):
    if request.method == 'POST':
        form = NewRegister(request.POST, request.FILES)
        # print (request.POST)
        if form.is_valid():
            try:
                first_name, last_name = request.POST['name'].split(' ', 1)
            except:
                first_name = request.POST['name']
                last_name = ""
            # print (form.cleaned_data.get('date_of_joining'))
            profile = form.save(commit=False)
            profile.reg_no = reg_no_gen(profile.programme, profile.branch, profile.year_of_admission)
            profile.country = request.POST['country']
            profile.state = request.POST['state']
            profile.city = request.POST['city']
            password = User.objects.make_random_password(length=10)
            # password = '12345678'
            user = User.objects.create_user(
                username=str(form.cleaned_data.get('roll_no')),
                first_name=first_name,
                last_name=last_name,
                email=str(form.cleaned_data.get('email')),
                password=password,
                is_active=True
            )
            profile.user = user
            profile.save()
            mappt = addPoints({'city': str(request.POST['city']), 'state': str(request.POST['state']),
                               'country': str(request.POST['country'])})
            print('Adding Map Point Status: ' + str(mappt))
            return render(request, 'AlumniConnect/confirm_email.html')
    else:
        form = NewRegister()
    return render(request, 'AlumniConnect/profileedit.html', {'form': form, 'edit': False})


@custom_login_required
def profileedit(request, id):
    if request.user.username == id:
        profile = Profile.objects.get(roll_no=id)
        if request.method == 'POST':
            form = ProfileEdit(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                profile = form.save()
                profile.save()
                return HttpResponseRedirect('/profile/' + id)
        else:
            print("here")
            form = ProfileEdit(instance=profile)
        return render(request, 'AlumniConnect/profileedit.html',
                      {'form': form, 'C': profile.country, 's': profile.state, 'c': profile.city, 'edit': True})
    else:
        return HttpResponseRedirect('/')


def activate(request, uidb64, token):
    print('inside activate')
    try:
        uid = urlsafe_base64_decode(uidb64)
        print(uid)
        u = User.objects.get(pk=uid)
        print(u)
        profile = Profile.objects.get(user=u)
    except(TypeError, ValueError, OverflowError):
        u = None
        profile = None
    
    # do not log in users with complete profiles
    if profile and (profile.verify or profile.reg_no):
        messages.warning(request, 'Please log in through password.')
        return redirect('/')

    if u and account_activation_token.check_token(u, token):
        u.is_active = True
        u.save()
        login(request, u)
        # return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
        messages.success(request, "Account Activated Successfully!")
        return HttpResponseRedirect('/complete_profile/')
    else:
        return HttpResponse('Activation link is invalid!')
    return redirect('/')

'''
    Incase the user does not complete their profile while the link
    is active they can generate a new link by providing the old link.
'''
def resend_activation(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        print(uid)
        u = User.objects.get(pk=uid)
        profile = Profile.objects.get(user = u)
    except(TypeError, ValueError, OverflowError):
        u = None
        profile = None
        return HttpResponse('Invalid link')
    
    # if complete profile action is completed, but admin has not ver
    if profile and (profile.verify or profile.reg_no):
        messages.success(request, "You have already completed your profile!")
        return redirect('/')

    # if user requests for a new link while the previous link is valid. 
    if account_activation_token.check_token(u, token):
        messages.success(request, "Link is currently active!")
        return redirect('/')
    
    # make new activation link 
    if u and profile and not account_activation_token.check_token(u, token):
            
            # re-sending mail for activation
            current_site = get_current_site(request)
            from_email = settings.DEFAULT_FROM_EMAIL
            to = [u.email]
            subject = "[noreply] SAC Account Activation"
            html_message = render_to_string('AlumniConnect/account_activation_email.html', {
                'user':u,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(u.pk)),
                'token':account_activation_token.make_token(u)
            })
            plain_message = strip_tags(html_message)
            send_mail(
                subject = subject,
                message = plain_message,
                from_email = from_email,
                recipient_list=to,
                html_message = html_message,
                fail_silently=False,
            )
            messages.success("Mail sent successfully.")
            return render(request,"AlumniConnect/confirm_email.html")
    else:
        messages.error('Something went wrong.')
        return redirect('/')

@custom_login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'AlumniConnect/change_password.html', {'form': form})
