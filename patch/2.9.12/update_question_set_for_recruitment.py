from irhrs.recruitment.models.job import Job
from irhrs.recruitment.models.question import QuestionSet


def update_question_set_in_job(job_slug, question_set_id):
    try:
        job = Job.objects.get(slug=job_slug)
        question_set = QuestionSet.objects.get(id=question_set_id)

        hiring_info = job.hiring_info
        if not hiring_info:
            print("hiring_info for given job_id not found.")
            return

        pre_screening_interview_detail = hiring_info.get('pre_screening_interview', None)
        if not pre_screening_interview_detail:
            print("Pre-screening Interview not found.")
            return

        expected_pre_screening_interview_detail = {
            "id": question_set_id,
            "name": question_set.name,
            "title": ""
        }
        hiring_info["pre_screening_interview"] = expected_pre_screening_interview_detail
        job.hiring_info = hiring_info
        job.save()

        print("Successfully updated question set.")

    except (Job.DoesNotExist, QuestionSet.DoesNotExist):
        print("Either job_slug or question_set_id is incorrect.")


job_slug = str(input("Enter Job Slug: "))
question_set_id = int(input("Enter New Question Set ID: "))

update_question_set_in_job(job_slug, question_set_id)
