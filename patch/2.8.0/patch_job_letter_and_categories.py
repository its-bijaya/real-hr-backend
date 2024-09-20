from irhrs.recruitment.models import Job, PreScreening


def update_job_template_letter_and_categories():
    """
    Add categories in job hiring info to ['A', 'B', 'C']
    Remove email template from pre screening
    """
    for job in Job.objects.all():

        # Add categories
        if not isinstance(job.hiring_info, dict):
            job.hiring_info = dict()

        job.hiring_info['categories'] = ['A', 'B', 'C']

        try:
            # delete letter from hiring_info field
            del job.hiring_info['pre_screening_letter']
        except KeyError:
            pass
        job.save()

    # delete letter from all Pre Screening
    PreScreening.objects.update(email_template=None)
