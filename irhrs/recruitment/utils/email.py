"""@irhrs_docs"""
import logging
import re

from django.conf import settings
from django.template.loader import render_to_string
from django_q.tasks import async_task

from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.custom_mail import custom_mail as send_mail

logger = logging.getLogger(__name__)

INFO_EMAIL = getattr(settings, 'INFO_EMAIL', 'noreply@realhrsoft.com')


def generate_html_message(context):
    message = context.get('message', '')
    context.update({
        'message': message.replace('\n', '<br>')
    })
    return render_to_string(
        'notifications/notification_base.html',
        context=context
    )


def replace_template_message(replace_data, template_message):
    message = template_message
    for r in re.findall('\{\{[A-Za-z0-9 _]+\}\}', message):
        message = message.replace(
            r,
            str(replace_data.get(r, ''))
        )
    return message


def generate_no_objection_template_letter_content(no_objection_letter, **kwargs):

    replace_data = {
        '{{full_name}}': no_objection_letter.responsible_person.full_name,
        '{{job_title}}': kwargs['job_title'],
        '{{published_date}}': kwargs['published_date'],
        '{{deadline}}': kwargs['deadline'],
        '{{job_url}}': kwargs['job_url']
    }

    message = kwargs['template_message']
    return replace_template_message(replace_data, message)


def send_no_objection_email(no_objection, make_async=True):
    """
    :param no_objection: no objection instance
    :param make_async: to send email asynchronously
    :return:
    """
    data = dict()
    data['job_title'] = str(no_objection.job)
    data['published_date'] = no_objection.job.posted_at.astimezone(
        ).strftime('%Y-%m-%d %I:%M %p')
    data['deadline'] = no_objection.job.deadline.astimezone(
        ).strftime('%Y-%m-%d %I:%M %p')
    data['job_url'] = no_objection.job.frontend_link
    data['template_message'] = no_objection.email_template.message

    subject = 'No Objection Letter'
    content = generate_no_objection_template_letter_content(no_objection, **data)

    if make_async:
        async_task(
            send_mail,
            subject,
            content,
            get_system_admin().email,
            [no_objection.responsible_person.email],
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )
    else:
        send_mail(
            subject,
            content,
            get_system_admin().email,
            [no_objection.responsible_person.email],
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )
    logger.info(
        f"Sent no objection letters of job {data['job_title']}"
    )


def send_custom_mail(subject, template_message, email, candidate_name='', job_title=''):

    replace_data = {
        "{{job_title}}": job_title,
        "{{candidate_name}}": candidate_name
    }

    content = replace_template_message(replace_data, template_message=template_message)

    subject = subject

    async_task(
        send_mail,
        subject,
        content,
        get_system_admin().email,
        [email],
        html_message=generate_html_message({
            'title': subject,
            'subtitle': subject,
            'message': content
        })
    )


def send_email(instance, for_candidate=False, make_async=True):
    """
    :param instance: Question answer instance or parent instance
    :param make_async: to send email asynchronously
    :param for_candidate: email send to candidate or external user
    :return:
    """

    replace_data = dict()

    if for_candidate:
        if not instance.email_template:
            return

        # Always should be called from parent instance
        template_message = instance.email_template.message
        email = instance.job_apply.candidate_email
        job_title = instance.job_apply.job_title

        replace_data['{{job_title}}'] = job_title
        replace_data['{{full_name}}'] = instance.job_apply.candidate_name
        replace_data['{{candidate_name}}'] = instance.job_apply.candidate_name
    else:
        if not instance.parent.email_template_external:
            return

        template_message = instance.parent.email_template_external.message
        email = instance.external_user.user.email
        job_title = instance.parent.job_apply.job_title

        replace_data['{{full_name}}'] = nested_getattr(
            instance, 'external_user.user.name') or nested_getattr(
            instance, 'external_user.user.full_name')
        replace_data['{{job_title}}'] = job_title
        replace_data['{{candidate_name}}'] = instance.parent.job_apply.candidate_name
        replace_data['{{link}}'] = instance.frontend_link

    content = replace_template_message(replace_data, template_message=template_message)

    class_name = instance.__class__.__name__
    subject = f'Request for {class_name}'

    if make_async:
        async_task(
            send_mail,
            subject,
            content,
            get_system_admin().email,
            [email],
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )
    else:
        send_mail(
            subject,
            content,
            get_system_admin().email,
            [email],
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )

    logger.info(
        f"Sent {class_name} letters for job {job_title}"
    )


def send_salary_declaration_email(salary_declaration, make_async=True):
    """
    :param salary_declaration: salary_declaration instance
    :param make_async: to send email asynchronously
    :return:
    """

    template_message = salary_declaration.email_template.message

    replace_data = {
        '{{full_name}}': salary_declaration.job_apply.candidate_name,
        '{{job_title}}': salary_declaration.job_apply.job_title,
        '{{link}}': salary_declaration.frontend_link,
        '{{salary}}': salary_declaration.salary,
    }

    content = replace_template_message(replace_data, template_message=template_message)

    subject = 'Request for Salary Declaration'

    if make_async:
        async_task(
            send_mail,
            subject,
            content,
            get_system_admin().email,
            [salary_declaration.job_apply.applicant.user.email],
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )
    else:
        send_mail(
            subject,
            content,
            get_system_admin().email,
            [salary_declaration.job_apply.applicant.user.email],
            html_message=generate_html_message({
                'title': subject,
                'subtitle': subject,
                'message': content
            })
        )
    logger.info(
        f"Sent salary declaration letters for job {salary_declaration.job_apply.job_title}"
    )
