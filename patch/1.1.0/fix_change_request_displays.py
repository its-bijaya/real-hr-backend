from irhrs.users.models import ChangeRequestDetails

base = ChangeRequestDetails.objects.only(
    'new_value_display', 'old_value_display'
)
old_display = base.filter(
    old_value_display__startswith='[',
    old_value_display__endswith=']'
).only('id')

new_display = base.filter(
    new_value_display__startswith='[',
    new_value_display__endswith=']'
)

print('Patching old value displays')
for cr in old_display:
    old = cr.old_value_display
    new = old[1:-1]
    cr.old_value_display = new
    cr.save(update_fields=['old_value_display'])
    print(
        cr.id, old, new
    )


print('Patching new value displays')
for cr in new_display:
    old = cr.new_value_display
    new = old[1:-1]
    cr.new_value_display = new
    cr.save(update_fields=['new_value_display'])
    print(
        cr.id, old, new
    )
