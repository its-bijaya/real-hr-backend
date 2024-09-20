from irhrs.payroll.models import UserVoluntaryRebate, User, RebateSetting, \
    UserVoluntaryRebateAction
from irhrs.payroll.utils.user_voluntary_rebate import get_default_fiscal_months_amount


def main():
    # Create rebate for those users who haven't requested rebate yet
    user_list = []
    count = 0
    rebate = RebateSetting.objects.get(title="LBRF")
    fiscal_year_id = 8
    organization = 1
    for user in User.objects.all().current():
        if not UserVoluntaryRebate.objects.filter(user=user).exists():
            print(f"Creating user voluntary rebate for {user.full_name}")
            user_rebate = UserVoluntaryRebate.objects.create(
                 title=rebate.title,
                 rebate=rebate,
                 description=rebate.title,
                 user=user,
                 fiscal_year_id=fiscal_year_id,
                 duration_unit="Monthly",
                 amount=0,
                 fiscal_months_amount=get_default_fiscal_months_amount(organization, fiscal_year_id)
            )
            user_list.append(user),
            print(f"Created user voluntary successfully for {user.full_name}")
            print(f"\n\n Creating rebate action for {user.full_name}")
            UserVoluntaryRebateAction.objects.create(
                 user_voluntary_rebate=user_rebate,
                 action="Approved",
                 remarks="Created by system"
            )
            count += 1
            print(f"Created successfully for {user.full_name} \n")
            print(f"Successfully created for {count} users\n\n")

    print(f"User voluntary rebate created for {count} users: ", user_list)


if __name__ == "__main__":
    main()
