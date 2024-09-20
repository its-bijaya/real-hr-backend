# Generated by Django 3.2.12 on 2023-12-08 03:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_alter_useremailunsubscribe_email_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useremailunsubscribe',
            name='email_type',
            field=models.PositiveIntegerField(choices=[(1, 'Birthday Email'), (2, 'Anniversary Email'), (3, 'Holiday Email'), (4, 'When you are invited to an event or meeting'), (5, 'When an event or meeting, you are involved, is updated'), (6, 'When an event or meeting, you are involved, is cancelled'), (40, 'When an assessment is assigned or unassigned to a user.'), (41, 'When an user completes an assigned assessment(For HR Only)'), (27, 'When a credit hour approval is requested/forwarded'), (28, 'When credit hour request is approved/declined'), (42, "When an employee's expiry date is in critical date range(For HR only)."), (43, 'When a training is assigned or unassigned.'), (44, 'When a training is deleted or cancelled.'), (45, 'When a training is requested by user(For HR only).'), (47, 'When a training request is acted upon.'), (46, 'When a training is updated.'), (48, 'When a user sends a resignation request.'), (49, 'When HR takes an action on resignation request.'), (50, 'When HR does not take action on resignation request for a certain interval(For HR only).'), (51, 'When user requests for Advance expenses'), (52, 'When user requests for settlement'), (18, 'When overtime is generated'), (57, 'When overtime is re-calibrated'), (58, 'When overtime claim request is sent'), (59, 'When overtime claim request is approved/declined/confirmed'), (60, 'When unclaimed overtime is expired'), (53, 'When requests is Approved and Denied for request of Advance expenses'), (54, 'When requests for settlement Approved or Denied'), (55, 'When HR has to settle the settlement request approved by approval levels'), (56, 'When HR cancels the approved advance expense request'), (71, 'When attendance adjustment is requested by user'), (72, 'When attendance adjustment is approved or declined by supervisor'), (73, 'When attendance adjustment is approved, declined or deleted by hr'), (74, 'When travel attendance request is sent by user'), (75, 'When travel attendance request is approved or declined'), (76, 'When credit hour delete request is requested/forwarded'), (77, 'When credit hour delete request is approved/declined'), (78, 'When credit hour is requested on behalf'), (35, 'When HR forward Payroll to approval levels for approval'), (79, 'When approval level approve or denies the payroll'), (80, 'When payroll is confirmed by HR after approval from appoval levels'), (81, 'When Payroll is acknowledged by user'), (82, 'When rebate is requested by user'), (83, 'When rebate is approved/decline by hr'), (84, 'When Rebate is requested by hr on behalf of user'), (85, 'When advance salary is requested by user'), (86, 'When level of approval decline/approved the advance salary'), (87, 'When hr generates the approved advance salary'), (88, 'When leave is deducted by the penalty')]),
        ),
    ]
