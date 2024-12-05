from django.shortcuts import render
from .models import Job
from datetime import date
from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse_lazy


def is_superuser(user):
    return user.is_superuser


@login_required
def index(request):
    jobs = Job.objects.all().filter(active=True).order_by('-posting_date')
    total_jobs = len(jobs)

    page_no = request.GET.get('page', 1)
    if jobs:
        paginator = Paginator(jobs, 10)
        try:
            current_page = paginator.page(page_no)
        except PageNotAnInteger:
            current_page = paginator.page(1)
        except EmptyPage:
            current_page = paginator.page(paginator.num_pages)
            
        # if request.user.is_superuser:
        #     ls = []
        #     for i in jobs:
        #         ls.append(i.person)
        #     ls1 = zip(current_page, ls)
        #     return render(request, "job_posting/index.html", {'ls1': ls1, 'current_page': current_page, 'total': total})
        # else:
        #     ls = []
        #     for i in jobs:
        #         ls.append(i.person)
        #     ls1 = zip(current_page, ls)

        return render(request, "job_posting/index.html", {'job_list': current_page, 'current_page': current_page, 'total': total_jobs})
    else:
        empty_list = []
        return render(request, "job_posting/index.html", {'job_list': empty_list, 'total': total_jobs})


@login_required
def filter_jobs(request):
    viewname = "filter"
    job_role = request.POST.get('job_role')
    page = request.GET.get('page', 1)
    job_type = request.POST.get('job_type')

    jobs = Job.objects.filter(active=True).order_by('-posting_date')

    if job_role != "all":
        jobs = jobs.filter(job_role = job_role)
    
    if job_type != "all":
        jobs = jobs.filter(job_type = job_type)

    #if user choose other in role here than no jobs will be shown :(
    # if job_role != 'all' and type != 'all':
    #     jobs = Job.objects.filter(job_role=job_role, job_type=job_type, active=True).order_by('-posting_date')
    # elif job_role != 'all' and type == 'all':
    #     jobs = Job.objects.filter(job_role=job_role, active=True).order_by('-posting_date')
    # elif job_role == 'all' and type != 'all':
    #     jobs = Job.objects.filter(type=type, active=True).order_by('-posting_date')
    # else:
    #     return redirect('jobs:index', permanent=True)

    if jobs:
        messages.success(request, "Found " + str(jobs.count()) + " jobs matching your query!")

        paginator = Paginator(jobs, 10)
        try:
            current_page = paginator.page(page)
        except PageNotAnInteger:
            current_page = paginator.page(1)
        except EmptyPage:
            current_page = paginator.page(paginator.num_pages)

        # ls = []
        # for i in posts:
        #     ls.append(i.person)
        #     ls1 = zip(ls2, ls)
        return render(request, "job_posting/index.html", {'job_list': current_page, 'current_page': current_page, 'viewname': viewname})

    else:
        empty_list = []
        messages.error(request, "No jobs matching your current requirements.")
        return render(request, "job_posting/index.html", {'job_list': empty_list ,'viewname': viewname})


@login_required
def post_opportunity(request):
    if request.method == 'POST':
        try:
            job_type = request.POST.get('job_type')
            job_role = request.POST.get('job_role')
            org_name = request.POST.get('org_name')
            location = request.POST.get('location')
            raw_link = request.POST.get('link')
            link = raw_link if raw_link.startswith('https://') or raw_link.startswith(
                'http://') else 'https://' + raw_link

            job_desc = request.POST.get('job_desc')
            stipend = int(request.POST.get('stipend')) if request.POST.get('stipend') else None
            exp_req = int(request.POST.get('exp_req')) if request.POST.get('exp_req') else None
            tenure = int(request.POST.get('tenure')) if request.POST.get('tenure') else None
            last_date = request.POST.get('last_date') if request.POST.get('last_date') else None
            join_date = request.POST.get('join_date') if request.POST.get('join_date') else None
            added_by = User.objects.get(username=str(request.user))

            if job_role == "Other":
                job_role = request.POST.get('other_jobrole')
            
            job_role = job_role.title()
            org_name = org_name.title()
            location = location.title()

            Job.objects.create(
                job_type=job_type,
                job_role=job_role,
                org_name=org_name,
                location=location,
                job_desc=job_desc,
                stipend=stipend,
                exp_req=exp_req,
                last_date=last_date,
                join_date=join_date,
                tenure=tenure,
                link=link,
                posting_date=date.today(),
                added_by=added_by,
                active=True )
            messages.success(request, "Job opportunity added successfully!")

        except Exception as e:
            messages.error(request, "Some error occurred, try again.")

        return redirect('jobs:index', permanent=True)

    return render(request, "job_posting/add_job.html")


@login_required
@user_passes_test(
    is_superuser, redirect_field_name=None,
    login_url=reverse_lazy('home')
)
def delete_job(request, job_id=None):
    if job_id:
        job_post = Job.objects.get(id=job_id)
        job_post.active = False
        job_post.save()
        messages.success(request, "Job opportunity removed successfully!")

    return redirect('jobs:index', permanent=True)
