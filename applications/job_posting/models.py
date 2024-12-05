from django.db import models
from django.contrib.auth.models import User


class Job(models.Model):
    job_role = models.CharField(max_length=20, null=False)#position
    org_name = models.CharField(max_length=25, null=False)#company
    job_type = models.CharField(max_length=20)#type
    link = models.URLField(max_length=1000)
    stipend = models.IntegerField(null=True, blank=True)
    exp_req = models.IntegerField(null=True, blank=True)
    tenure = models.IntegerField(null=True, blank=True)
    last_date = models.DateField(null=True, blank=True)
    join_date = models.DateField(null=True, blank=True)
    job_desc = models.CharField(max_length=300, help_text="Brief Description of job profile", null=True, blank=True)#desc
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)#person
    posting_date = models.DateField()
    location = models.CharField(max_length=30, null=False)
    active = models.BooleanField(null=False, default=True)

    def __str__(self):
        return self.job_role  + " at " + self.org_name
