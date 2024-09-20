"""Copy user detail from current experience"""


from django.contrib.auth import get_user_model

from irhrs.users.models import UserExperience

User = get_user_model()
ORGANIZATION_SLUG = "twitter"


def main():
    count = 0
    for experience in UserExperience.objects.filter(
        organization__slug=ORGANIZATION_SLUG, is_current=True
    ).select_related(
        "user", "user__detail", "branch", "division", "employment_status",
        "employee_level", "job_title"
    ):
        user_detail = experience.user.detail
        user_detail.branch = experience.branch
        user_detail.division = experience.division
        user_detail.job_title = experience.job_title
        user_detail.employment_level = experience.employee_level
        user_detail.employment_status = experience.employment_status
        user_detail.save()
        count += 1
        print(f"Saving {count} user details.", end="\r")

    print(f"Successfully saved {count} user details.")


if __name__ == "__main__":
    main()
