import json

from django.db import transaction
from django.core.management import call_command

from irhrs.task.models import Task
from irhrs.task.models.project import TaskProject
from irhrs.task.models.settings import UserActivityProject, HOUR, Activity, Project


@transaction.atomic
def migrate_task_project_to_project():
    task_projects = TaskProject.objects.all()

    projects = Task.objects.filter(project__isnull=False)
    f = open('project.json', 'w')
    json.dump(list(projects.values('id', 'project')), f, default=str)
    f.close()
    projects.update(project=None)
    call_command('migrate')

    print(f'{task_projects.count()} tasks are about to migrate.')
    for index, task in enumerate(task_projects):
        # Avoid IntegrityError while re-running script
        Project.objects.filter(name=task.name).delete()
        project = Project.objects.create(
            name=task.name,
            description=task.description,
            is_billable=False
        )
        # Avoid IntegrityError while re-running script
        Activity.objects.filter(name=f"Default{index+1}").delete()
        activity = Activity.objects.create(
            name=f"Default{index+1}",
            description="Default activity for patch.",
            unit=HOUR,
            employee_rate=0,
            client_rate=0,
        )
        users = task.members.all().distinct()
        print(f'{users.count()} members are migrating from {task} to {project}.')
        for user in users:
            UserActivityProject.objects.create(
                project=project,
                user=user,
                activity=activity,
                is_billable=False,
                client_rate=0,
                employee_rate=0
            )

    # update Task with previous Project
    f = open('project.json', 'r')
    tasks = json.load(f)
    for task in tasks:
        tp = TaskProject.objects.get(id=task.get('project'))
        project = Project.objects.get(name=tp.name)
        Task.objects.filter(id=task.get('id')).update(
            project=project
        )
    f.close()
