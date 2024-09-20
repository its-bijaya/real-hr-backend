# ############## TARGET SERVER CODE ############## #
import json
from django.db import DatabaseError, transaction
from irhrs.payroll.api.v1.serializers import HeadingSerializer
from irhrs.payroll.models import Heading

with open('heading_dump.json', 'r') as fp:
    aayu_dict = json.load(fp)

@transaction.atomic()
def trnsatiomic(target_organization):
    for data in aayu_dict:
        data.update({
            'organization': target_organization
        })
    passes = True
    for hd in aayu_dict:
        print(hd.get('order'), hd.get('label'), hd.get('organization'))
        ser = HeadingSerializer(data=hd)
        if ser.is_valid():
            print('\tPass')
            ser.save()
        else:
            passes = False
            print('\t', ser.errors.values())
    if not passes:
        raise DatabaseError


org_list = [
    "naya-organization"
]
for org in org_list:
    if input(f'Remove Existing Heading for {org}') == 'y':
        Heading.objects.all().filter(organization__slug=org).delete()
    print('Running for', org)
    trnsatiomic(org)
