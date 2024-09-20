"""
Patch for Change request of UserAddress

Previously, country field of UserAddress was CharField which is converted into property and also
new country_ref field (Foreign Key to Country model) is added in replacement of country field. Due
to this, ChangeRequest have data of country field which should be changed to country_ref
"""
from irhrs.users.models import ChangeRequestDetails


def main():
    # make sure to run management command to seed location
    # ./manage.py seed_locations
    count = 0
    for detail in ChangeRequestDetails.objects.filter(change_field='country'):
        detail.change_field = 'country_ref'
        detail.new_value = 603
        detail.new_value_display = "Nepal"
        detail.save()
        count += 1
        print(f"Saving {count} change request details.", end="\r")


if __name__ == '__main__':
    main()
