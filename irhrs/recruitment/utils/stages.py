from rest_framework.exceptions import ValidationError
from functools import cached_property
from django.contrib.auth import get_user_model

from irhrs.recruitment.models import (
    PreScreening,
    PostScreening,
    JobApply,
    JobApplyStage,
    PreScreeningInterview,
    Assessment,
    QuestionSet,
    Interview,
    ReferenceCheck,
    ReferenceChecker,
    SalaryDeclaration,
)

from irhrs.recruitment.constants import (
    APPLIED,
    REFERENCE_VERIFIED,
    SALARY_DECLARED,
    SCREENED,
    COMPLETED,
    SELECTED,
    SHORTLISTED,
    PRE_SCREENING_INTERVIEWED,
    ASSESSMENT_TAKEN,
    REJECTED,
    INTERVIEWED,
)
from irhrs.recruitment.models.applicant import ApplicantReference

USER = get_user_model()

display_name_mapper = {
    APPLIED: "Application Received",
    SCREENED: "Preliminary Shortlist",
    SHORTLISTED: "Final Shortlist",
    PRE_SCREENING_INTERVIEWED: "Preliminary Screening Interview",
    ASSESSMENT_TAKEN: "Assessment",
    INTERVIEWED: "Interview",
    REFERENCE_VERIFIED: "Reference Check",
    SALARY_DECLARED: "Salary Declaration",
    SELECTED: "Selected Candidate",
    REJECTED: "Rejected Candidate",
}

score__gte__mapper = {
    SCREENED: "pre_screening__score__gte",
    PRE_SCREENING_INTERVIEWED: "pre_screening_interview__score__gte",
    ASSESSMENT_TAKEN: "assessment__score__gte",
    REFERENCE_VERIFIED: "reference_check__score__gte",
}

stage_is_null_mapper = {
    SCREENED: "pre_screening__isnull",
    SHORTLISTED: "post_screening__isnull",
    PRE_SCREENING_INTERVIEWED: "pre_screening_interview__isnull",
    ASSESSMENT_TAKEN: "assessment__isnull",
    INTERVIEWED: "interview__isnull",
    REFERENCE_VERIFIED: "reference_check__isnull",
    SALARY_DECLARED: "salary_declarations__isnull",
}

letter_mapper = {
    SCREENED: "pre_screening_letter",
    SHORTLISTED: "post_screening_letter",
    PRE_SCREENING_INTERVIEWED: "pre_screening_interview_letter",
    INTERVIEWED: "interview_letter",
    ASSESSMENT_TAKEN: "assessment_letter",
    REFERENCE_VERIFIED: "reference_check_letter",
    SALARY_DECLARED: "salary_declaration_letter",
}

stage_mapper = {
    SCREENED: "pre_screening",
    SHORTLISTED: "post_screening",
    PRE_SCREENING_INTERVIEWED: "pre_screening_interview",
    INTERVIEWED: "interview",
    ASSESSMENT_TAKEN: "assessment",
    REFERENCE_VERIFIED: "reference_check",
    SALARY_DECLARED: "salary_declaration",
}

class_mapper = {
    SCREENED: PreScreening,
    SHORTLISTED: PostScreening,
    PRE_SCREENING_INTERVIEWED: PreScreeningInterview,
    ASSESSMENT_TAKEN: Assessment,
    INTERVIEWED: Interview,
    REFERENCE_VERIFIED: ReferenceCheck,
    SALARY_DECLARED: SalaryDeclaration,
    SELECTED: None,
    REJECTED: None,
}

def get_next_stage(job, current):
    NO_NEXT_STAGE = ""
    stages = job.stages
    if current not in stages:
        raise ValidationError(f"{current} stage is not in job stages")

    index = stages.index(current)

    if index + 1 > len(stages):
        return NO_NEXT_STAGE

    next_stage = stages[index + 1]
    return next_stage

def get_stage_filters(job, stage, is_null):
    next_stage = get_next_stage(job, stage)
    filters = {"job_apply__job" : job}
    if next_stage not in [SELECTED, REJECTED]:
        next_stage_is_null = f"job_apply__{stage_is_null_mapper[next_stage]}"
        filters[next_stage_is_null] = is_null
    return filters

class RecruitmentProcess:
    stage = ""

    def __init__(self, data, job, current_stage):
        self.data = data
        self.job = job
        self.current_stage = self.stage or current_stage

    def get_applications_filters(self):
        filters = {
            "job": self.job,
            stage_is_null_mapper[self.current_stage]: False,
        }
        if self.next_stage not in [SELECTED, REJECTED]:
            filters[stage_is_null_mapper[self.next_stage]] = True
        return filters

    def get_applications(self):
        applications = JobApply.objects.filter(**self.get_applications_filters())
        categories = self.data.get("categories", [])
        score = self.data.get("score")
        if categories:
            job_categories = self.job.hiring_info.get("categories", [])
            valid_categories = set(job_categories).intersection(set(categories))
            applications = applications.filter(
                assessment__category__in=valid_categories
            )

        rejected_candidates = None
        if score and isinstance(score, (int, float)):
            score__gte = score__gte__mapper.get(self.current_stage)
            if score__gte:
                applications = applications.filter(**{score__gte: score})
                rejected_candidates = applications.exclude(
                    **{score__gte: score}
                ).values_list("id", flat=True)

        if rejected_candidates:
            JobApply.objects.filter(id__in=rejected_candidates).update(
                status=REJECTED
            )
            JobApplyStage.objects.bulk_create(
                [
                    JobApplyStage(job_apply_id=job_apply_id, status=REJECTED)
                    for job_apply_id in rejected_candidates
                ]
            )
        return applications

    @cached_property
    def next_stage(self):
        NO_NEXT_STAGE = ""
        stages = self.job.stages
        index = stages.index(self.current_stage)
        if index + 1 > len(stages):
            return NO_NEXT_STAGE
        return stages[index + 1]

    def get_responsible_person(self):
        assigned_to = self.data.get("responsible_person")
        return (
            USER.objects.filter(id=assigned_to).first()
            if assigned_to and (isinstance(assigned_to, int) or assigned_to.isdigit())
            else None
        )

    def complete_current_stage(self):
        applications = self.get_applications()
        applications.update(status=self.current_stage)
        application_ids = applications.values("id")

        JobApplyStage.objects.bulk_create(
            [
                JobApplyStage(
                    job_apply_id=application.get("id"), status=self.current_stage
                )
                for application in application_ids
            ]
        )

    def get_letter_template(self):
        letter = letter_mapper.get(self.current_stage)
        if not letter:
            return {}
        if not (self.job.hiring_info and self.job.hiring_info.get(letter)):
            return {}
        return {"email_template_id": self.job.hiring_info.get(letter).get("id")}

    def send_emails(self, instances):
        if not self.get_letter_template():
            return

        for instance in instances:
            instance.send_mail()

    def get_question_set(self):
        """"""
        question_set = self.data.get("question_set")
        return (
            QuestionSet.objects.filter(id=question_set).first()
            if question_set and question_set.isdigit()
            else None
        )

    def get_request_data(self):
        data = self.data
        return {
            "categories": data.get("categories", []),
            "score": data.get("score"),
            "assigned_to": data.get("assigned_to"),
            "question_set": data.get("question_set"),
        }

    def set_screened(self):
        job_apply_ids = self.get_applications().values_list("id", flat=True)
        return PreScreening.objects.bulk_create(
            [
                PreScreening(
                    responsible_person=self.get_responsible_person(),
                    question_set=self.get_question_set(),
                    job_apply_id=apply_id,
                    **self.get_letter_template(),
                )
                for apply_id in job_apply_ids
            ]
        )

    def set_shortlisted(self):
        return PostScreening.objects.bulk_create(
            [
                PostScreening(
                    job_apply_id=apply_id,
                    responsible_person=self.get_responsible_person(),
                    question_set=self.get_question_set(),
                    **self.get_letter_template(),
                )
                for apply_id in self.get_applications().values_list("id", flat=True)
            ]
        )

    def set_pre_screening_interviewed(self):
        return PreScreeningInterview.objects.bulk_create(
            [
                PreScreeningInterview(
                    job_apply_id=apply_id,
                    responsible_person=self.get_responsible_person(),
                    question_set=self.get_question_set(),
                    **self.get_letter_template(),
                )
                for apply_id in self.get_applications().values_list("id", flat=True)
            ]
        )

    def set_assessment_taken(self):
        return Assessment.objects.bulk_create(
            [
                Assessment(
                    job_apply_id=apply_id,
                    responsible_person=self.get_responsible_person(),
                    question_set=self.get_question_set(),
                    **self.get_letter_template(),
                )
                for apply_id in self.get_applications().values_list("id", flat=True)
            ]
        )

    def set_interviewed(self):
        return Interview.objects.bulk_create(
            [
                Interview(
                    job_apply_id=apply_id,
                    question_set=self.get_question_set(),
                    **self.get_letter_template(),
                )
                for apply_id in self.get_applications().values_list("id", flat=True)
            ]
        )

    def set_reference_verified(self):
        job_apply_ids = list(self.get_applications().values_list("id", flat=True))
        references = ReferenceCheck.objects.bulk_create(
            [
                ReferenceCheck(job_apply_id=apply_id, **self.get_letter_template())
                for apply_id in job_apply_ids
            ]
        )
        applicant_references = ApplicantReference.objects.filter(
            applicant_id__in=job_apply_ids
        ).values_list('id', flat=True)

        ReferenceChecker.objects.bulk_create(
            [ReferenceChecker(user_id=reference) for reference in applicant_references],
        )

        return references

    def set_salary_declared(self):
        instances = SalaryDeclaration.objects.bulk_create(
            [
                SalaryDeclaration(job_apply_id=application.get("id"))
                for application in self.get_applications().values("id")
            ]
        )
        return instances

    def set_selected(self):
        job_apply_ids = self.get_applications().values_list("id", flat=True)
        JobApply.objects.filter(id__in=job_apply_ids).update(status=SELECTED)
        return JobApplyStage.objects.bulk_create(
            [
                JobApplyStage(job_apply_id=job_apply_id, status=SELECTED)
                for job_apply_id in job_apply_ids
            ]
        )

    def set_rejected(self):
        job_apply_ids = self.get_applications().values_list("id", flat=True)
        JobApply.objects.filter(id__in=job_apply_ids).update(status=REJECTED)
        return JobApplyStage.objects.bulk_create(
            [
                JobApplyStage(job_apply_id=job_apply_id, status=REJECTED)
                for job_apply_id in job_apply_ids
            ]
        )

    def forward(self):
        """
        we can forward to any stage so we need to create the instances accordingly.
        """
        self.complete_current_stage()
        instances = getattr(self, f"set_{self.next_stage}")()
        if self.next_stage in [SELECTED, REJECTED, SALARY_DECLARED]:
            return
        self.send_emails(instances)


class ApplicantInitialization(RecruitmentProcess):
    stage = APPLIED

    def get_applications(self):
        return JobApply.objects.filter(
            job=self.job, **{stage_is_null_mapper[self.next_stage]: True}
        ).exclude(status=REJECTED)


class PreScreeningStage(RecruitmentProcess):
    stage = SCREENED

    def set_shortlisted(self):
        return PostScreening.objects.bulk_create(
            [
                PostScreening(
                    job_apply_id=application.get("id"),
                    data=application.get("pre_screening__data"),
                    responsible_person=self.get_responsible_person(),
                    question_set_id=application.get("pre_screening__question_set"),
                    category=application.get("pre_screening__category"),
                    score=application.get("pre_screening__score"),
                    **self.get_letter_template(),
                )
                for application in self.get_applications().values(
                    "id",
                    "pre_screening__data",
                    "pre_screening__question_set",
                    "pre_screening__category",
                    "pre_screening__score",
                )
            ]
        )

    def get_applications(self):
        categories = self.data.pop('categories', [])
        applications = super().get_applications().exclude(
            status__in=[
                SELECTED,
                REJECTED
            ]
        )
        if categories:
            self.data['categories'] = categories
            applications = applications.filter(pre_screening__category__in=categories)
        return applications


class ReferenceCheckStage(RecruitmentProcess):
    stage = REFERENCE_VERIFIED

    def get_applications(self):
        applications = JobApply.objects.filter(
            job=self.job,
            reference_check__status=COMPLETED,
            reference_check__verified=True,
        ).exclude(
            status__in=[
                SELECTED,
                REJECTED
            ]
        )
        return applications


class SalaryDeclarationStage(RecruitmentProcess):
    stage = SALARY_DECLARED

    def set_selected(self):
        pass

    def get_applications(self):
        return super().get_applications().exclude(status__in=[SELECTED, REJECTED])
