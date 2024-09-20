dependents = None


def take_backup(apps, scheme):
    global dependents
    UserInsurance = apps.get_model('users', 'UserInsurance')
    dependents = list(
        UserInsurance.objects.all().values('id', 'dependent')
    )


def set_dependent(apps, scheme):
    global dependents
    UserInsurance = apps.get_model('users', 'UserInsurance')

    for datum in dependents:
        dependent = UserInsurance.objects.get(id=datum.get('id'))
        for key, value in datum.items():
            if key != 'id' and value:
                getattr(dependent, key).set([value])
    print(
        "\nChanged UserInsurance are: \n",
        list(
            map(
                lambda x: x.get('id'),
                dependents
            )
        )
    )
