from irhrs.users.models import UserDetail


def rename_nationality():
    updated_user_detail = UserDetail.objects.filter(
        nationality="Nepalese"
    ).update(nationality="Nepali")

    print('Total Updated User Detail: ', updated_user_detail)
