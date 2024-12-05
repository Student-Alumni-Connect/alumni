from django.urls import path, re_path

from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.index, name='index'),
    path('post/', views.post_opportunity, name='post'),
    path('filter/', views.filter_jobs, name='filter'),
    re_path(r'^del/(?P<job_id>[0-9]+)/$', views.delete_job, name='delete'),
]
