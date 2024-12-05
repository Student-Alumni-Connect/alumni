"""AlumniConnect URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from os import listdir
from .  import views


favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)
urlpatterns = []

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('', views.index, name='home'),
    path('admin/', admin.site.urls),
    path('login/', views.LoginFormView.as_view(), name='login'),
    #path('account/reset_password/', views.ResetPasswordRequestView.as_view(), name="reset_password"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/',views.signup, name = "signup"),
    path('register/', views.register, name='register'),
    path('newregister/', views.new_register, name='new_register'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.activate, name='activate'),
    path('confirm/', TemplateView.as_view(template_name='AlumniConnect/confirm_email.html'), name = 'confirm'),
    path('success/', TemplateView.as_view(template_name='AlumniConnect/account_success.html'), name = 'success'),
    re_path('^', include('django.contrib.auth.urls')),
    path('password/', views.change_password, name='change_password'),
    re_path(r'^profileedit/(?P<id>[a-zA-Z0-9]+)/$', views.profileedit, name='profileedit'),
    path('profile/', include('applications.alumniprofile.urls')),
    path('members/', include('applications.members.urls')),
    path('events/', include('applications.events_news.urls')),
    path('news/', include('applications.news.urls')),
    path('newsletter/', include('applications.publications.urls')),
    path('geolocation/', include('applications.geolocation.urls')),
    path('alumnibody/', views.alumniBody),
    path('alumnicard/', views.alumniCard, name='alumnicard'),
    path('gallery/', include('applications.gallery.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('awards/', include('applications.awards.urls')),
    path('chapter/', include('applications.chapter.urls')),
    path('adminportal/', include('applications.adminportal.urls')),
    path('jobs/', include('applications.job_posting.urls')),
    re_path(r'favicon.ico', favicon_view),
    path('constitution/', views.constitution, name='constitution'),
    path('blogs/', include('applications.blog.urls')),
    #path('', views.index, name='home'),
    path('check-email-exists/', views.check_email_exists, name='check_email_exists'),
]

if settings.DEBUG:
    

    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    
admin.site.site_header = "IIITDMJ Alumni Association"
admin.site.site_title = "Alumni Association"
admin.site.index_title = "Alumni Association Admin"
