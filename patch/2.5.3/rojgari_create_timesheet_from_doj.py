"""

SN	Name	Joined Date	Shift
1	Manoj Kumar Sunuwar	8/1/2019	10-6 pm
2	Upendra Gurung	8/18/2019	9.30-5.30 pm
3	Shree Krishna Rauniyar	8/11/2019	9.30-5.30 pm
4	Amita Shrestha	8/15/2019	9.00-5.00 pm
5	Yashoda Sodari	8/15/2019	9.30-5.30 pm
6	Gautam Chaudhary	11/1/2019	10-6 pm
7	Rajendra Karki	11/3/2019	9-5 pm

"""

# verbatim from core.realhrsoft.com API.

# name_to_email_map = {
#     'Bhuwan Pandit': 'bhuwan.pandit@rojogari.com',
#     'Ayoushma Khanal': 'ayoushma.khanal@rojgari.com',
#     'Shrijana Shrestha': 'shrijana.shrestha@rojgari.com',
#     'Madan Giri': 'madan.giri@rojgari.com',
#     'Diana Silwal Pradhan': 'diana.pradhan@realsolutions.com.np',
#     'Umesh Chaudhary': 'umesh.chaudhary@aayulogic.com',
#     'Shova Bakhu': 'shova.bakhu@rojgari.com',
#     'Raju Bhattarai': 'raju.bhattarai@aayulogic.com',
#     'Sumit Chhetri': 'sumit.chhetri@aayulogic.com',
#     'Ujwal Shrestha Lacoul': 'ujwal.shrestha@merojob.com',
#     'Reza Khanal': 'reza.khanal@merojob.com',
#     'Babin Subedi': 'babin.subedi@merojob.com',
#     'Santosh Aryal': 'santosh.aryal@aayulogic.com',
#     'Rajesh Manandhar': 'rajesh.manandhar@merojob.com',
#     'Priyanka Basnet': 'priyanka.basnet@merojob.com',
#     'Yagyashree Dahal': 'yagyashree.dahal@merojob.com',
#     'Nisha Gyawali': 'nisha.gyawali@merojob.com',
#     'Robijan Bajracharya': 'robijan.bajracharya@rojgari.com',
#     'Sulav Pandey': 'sulav.pandey@merojob.com',
#     'Prabesh Kunwar': 'prabesh.kunwar@merojob.com',
#     'Prahlad Shrestha': 'prahlad.shrestha@aayulogic.com',
#     'Anusha Poudyal': 'anusha.poudyal@merojob.com',
#     'Prabin Acharya': 'prabin.acharya@aayulogic.com',
#     'Rohit Shrestha': 'rohit.shrestha@merojob.com',
#     'Sanjeev Shrestha': 'sanjeev.shrestha@aayulogic.com',
#     'Mukesh Ghising': 'mukesh.ghising@merojob.com',
#     'Santosh Khanal': 'santosh.khanal@realsolutions.com.np',
#     'Alish Ratna Tamrakar': 'alish.tamrakar@merojob.com',
#     'Ajay Shrestha': 'ajay.shrestha@aayulogic.com',
#     'Pujan Shrestha': 'pujan.shrestha@aayulogic.com',
#     'Kopila Gotame': 'kopila.gotame@aayulogic.com',
#     'Benupama Karkee': 'benupama.karkee@realsolutions.com.np',
#     'Samikshya Dhakal': 'samikshya.dhakal@realsolutions.com.np',
#     'Sital Pokhrel': 'sital.pokhrel@merojob.com',
#     'Vikal Rajbanshi': 'vikal.rajbanshi@merojob.com',
#     'Sujeep Bajracharya': 'sujeep.bajracharya@merojob.com',
#     'Santosh Chaudhary': 'santosh.chaudhary@merojob.com',
#     'Reeya Balla': 'reeya.balla@merojob.com',
#     'Takchata Khatiwada': 'takchata.khatiwada@merojob.com',
#     'Siddhartha Jung Khadka': 'siddhartha.khadka@merojob.com',
#     'Siwan Raj KC': 'siwan.kc@merojob.com',
#     'Nisha Subedi': 'nisha.subedi@merojob.com',
#     'Bikesh Shahi': 'bikesh.shahi@merojob.com',
#     'Anmol Singh Rawal': 'anmol.rawal@merojob.com',
#     'Gautam Chaudhary': 'gautam.chaudhary@merojob.com',
#     'Elina Sapkota': 'elina.sapkota@merojob.com',
#     'Alisha Pandey': 'alisha.pandey@merojob.com',
#     'Upendra Gurung': 'upendra.gurung@merojob.com',
#     'Yashoda Sodari': 'yashoda.sodari@merojob.com',
#     'Amita Shrestha': 'amita.shrestha@merojob.com',
#     'Tirtha Raj Roshyara': 'tirtha.roshyara@merojob.com',
#     'Shree Krishna Rauniyar': 'shree.rauniyar@merojob.com',
#     'Manoj Kumar Sunuwar': 'manoj.sunuwar@merojob.com',
#     'Shital Babu Luitel': 'shital.luitel@aayulogic.com',
#     'Utshab Khadka': 'utshab.khadka@aayulogic.com',
#     'Aadesh Koirala': 'aadesh.koirala@merojob.com',
#     'Shruti Dutta': 'shruti.dutta@merojob.com',
#     'Ananda Pun Magar': 'ananda.magarp@merojob.com',
#     'Sanju Tamang': 'sanju.tamang@merojob.com',
#     'Sarottum Shrestha': 'sarottum.shrestha@realsolutions.com.np',
#     'Anura Rana': 'anura.rana@merojob.com',
#     'Sachin Shrestha': 'sachin.shrestha@merojob.com',
#     'Shankalpa Khadka': 'shankalpa.khadka@merojob.com',
#     'Bishwa Acharya': 'bishwa.acharya@merojob.com',
#     'Sachina Shrestha': 'sachina.shrestha@merojob.com',
#     'Kamala Khanal': 'kamala.khanal@aayulogic.com',
#     'Pratik Budhathoki': 'pratik.budhathoki@aayulogic.com',
#     'Merusha Adhikari': 'merusha.adhikari@merojob.com',
#     'Bishal Dahal': 'bishal.dahal@merojob.com',
#     'Rupesh Singh': 'rupesh.singh@aayulogic.com',
#     'Mahesh Manandhar': 'mahesh.manandhar@aayulogic.com',
#     'Pradeep Malakar': 'pradeep.malakar@merojob.com',
#     'Wangju Rumba': 'wangju.rumba@merojob.com',
#     'Jyotika Bhatt': 'jyotika.bhatt@realsolutions.com.np',
#     'Kajal Lama': 'kajal.lama@merojob.com',
#     'Rajani Chulyadyo': 'rajani.chulyadyo@aayulogic.com',
#     'Puja Sakha': 'puja.sakha@merojob.com',
#     'Dipesh Basnet': 'dipesh.basnet@aayulogic.com',
#     'Ankit Krishna Shrestha': 'ankit.shrestha@aayulogic.com',
#     'Manoj Thapa Shrestha': 'manoj.shrestha@aayulogic.com',
#     'Sujan Sitikhu': 'sujan.sitikhu@aayulogic.com',
#     'Shristi Khadka': 'shristi.khadka@merojob.com',
#     'Nikhil Rawal': 'nikhil.rawal@merojob.com',
#     'Ravi Adhikari': 'ravi.adhikari@aayulogic.com',
#     'Aishwarya Dhakhwa': 'aishwarya.dhakhwa@realsolutions.com.np',
#     'Ramesh Khatri': 'ramesh.khatri@aayulogic.com',
#     'Bishnu Karki': 'bishnu.karki@merojob.com',
#     'Sujan Chitrakar': 'sujan.chitrakar@merojob.com',
#     'Anurag Regmi': 'anurag.regmi@aayulogic.com',
#     'Shankar Pandey': 'shankar.pandey@aayulogic.com',
#     'Saroj Paudel': 'saroj.paudel@merojob.com',
#     'Bindeep Acharya': 'bindeep.acharya@aayulogic.com',
#     'Nirmaya Chhetri': 'nirmaya.chhetri@rojgari.com',
#     'Dilliram Dhakal': 'dilliram.dhakal@rojgari.com',
#     'Bhai Krishna Khadka': 'bhai.khadka@merojob.com',
#     'Sandip Balami': 'sandip.balami@rojgari.com',
#     'Kritika Katwal': 'kritika.katwal@merojob.com',
#     'Saurabh Poudel': 'saurabh.poudel@realsolutions.com.np',
#     'Kushal Bhandari': 'kushal.bhandari@rojgari.com',
#     'Anusha Shrestha': 'anusha.shrestha@merojob.com',
#     'Bishwo Maharjan': 'bishwo.maharjan@aayulogic.com',
#     'Jamuna Gautam': 'jamuna.gautam@merojob.com',
#     'Bikram Tamang': 'bikram.tamang@merojob.com',
#     'Dipesh Acharya': 'dipesh.acharya@merojob.com',
#     'Tarapati BC': 'tarapati.bc@rojgari.com',
#     'Rojina Shrestha': 'rojina.shrestha@merojob.com',
#     'Bindu Thapa': 'bindu.thapa@rojgari.com',
#     'Sukriti Shrestha': 'sukriti.shrestha@realsolutions.com.np',
#     'Ishika Shahi': 'ishika.shahi@rojgari.com',
#     'Mingma Dawa Sherpa': 'mingma.sherpa@merojob.com',
#     'Sabina Parajuli': 'sabina.parajuli@merojob.com',
#     'Sumit Dhital': 'sumit.dhital@rojgari.com',
#     'Rija Shakya': 'rija.shakya@merojob.com',
#     'Niroj Maharjan': 'niroj.maharjan@rojgari.com',
#     'Sajeena GurungPokharel': 'sajeena.gurung@merojob.com',
#     'Sneha Adhikari': 'sneha.adhikari@rojgari.com',
#     'Timila Mali': 'timila.mali@merojob.com',
#     'Shilpy Dawadi': 'shilpy.dawadi@rojgari.com',
#     'Sanjib Kumar Niraula': 'sanjib.niraula@rojgari.com',
#     'Rewati Ghimire': 'rewati.ghimire@merojob.com',
#     'Pingala Devi AcharyaSaraswoti': 'pingala.acharya@merojob.com',
#     'Sajina Maharjan': 'sajina.maharjan@merojob.com',
#     'Ram Sharan Khadka': 'ramsharan.khadka@rojgari.com',
#     'Bikash Dotel': 'bikash.dotel@rojgari.com',
#     'Muna Acharya Sharma': 'muna.acharya@rojgari.com',
#     'Rebekah Prateek Rai': 'rebekah.rai@merojob.com',
#     'Bigyan Prajapati': 'bigyan.prajapati@merojob.com',
#     'Parbata Rai': 'parbata.rai@realsolutions.com.np',
#     'Pashupati Khadka': 'pashupati.khadka@yahoo.com',
#     'Abhishek Bhakta Shrestha': 'abhishek.shrestha@merojob.com',
#     'Isha Giri': 'isha@realsolutions.com.np',
#     'Kriti Upreti': 'kriti.upreti@merojob.com',
#     'Nibha Shakya': 'nibha.shakya@merojob.com',
#     'Shanti Bhandari': 'shanti@merojob.com',
#     'Binod Magar': 'binod.thapa@merojob.com',
#     'Rajesh Shrestha': 'rajesh.shrestha@aayulogic.com',
#     'Shailendra Raj Giri': 'shail@merojob.com'
# }



from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from irhrs.attendance.models import TimeSheet, IndividualUserShift, WorkShift, IndividualAttendanceSetting
from irhrs.core.utils.common import get_today
from dateutil.rrule import rrule, DAILY
from datetime import datetime
from dateutil.parser import parse as date_parser

USER = get_user_model()


def double_print(*args, **kwargs):
    with open('patch_rojgari.log', 'a') as f:
        f.write(
            '    '.join(
                map(
                    str,
                    args
                )
            ).replace('\r', '')
        )
        f.write('\n')
    print(*args, **kwargs)


def daily_iterator(start, end):
    if isinstance(start, datetime):
        start = start.date()
    elif isinstance(start, str):
        start = date_parser(start).date()
    if isinstance(end, datetime):
        end = end.date()
    elif isinstance(end, str):
        end = date_parser(end).date()
    iterator = rrule(
        freq=DAILY,
        dtstart=start,
        until=end
    )
    return map(lambda dt: dt.date(), iterator)


current_employee_data = [
    {
        'email': 'manoj.sunuwar@merojob.com',
        'full_name': 'Manoj Kumar Sunuwar',
        'doj': '8/1/2019',
        'shift_name': 'Flex(9:30-17:30)'
    },
    {
        'email': 'upendra.gurung@merojob.com',
        'full_name': 'Upendra Gurung',
        'doj': '8/18/2019',
        'shift_name': 'Flex(9:30-17:30)'
    },
    {
        'email': 'shree.rauniyar@merojob.com',
        'full_name': 'Shree Krishna Rauniyar',
        'doj': '8/11/2019',
        'shift_name': 'Flex(9:30-17:30)'
    },
    {
        'email': 'amita.shrestha@merojob.com',
        'full_name': 'Amita Shrestha',
        'doj': '8/15/2019',
        'shift_name': 'Standard Working Time'
    },
    {
        'email': 'yashoda.sodari@merojob.com',
        'full_name': 'Yashoda Sodari',
        'doj': '8/15/2019',
        'shift_name': 'Flex(9:30-17:30)'
    },
    {
        'email': 'gautam.chaudhary@merojob.com',
        'full_name': 'Gautam Chaudhary',
        'doj': '11/1/2019',
        'shift_name': 'Flex(10:00-18:00)'
    }
]


def fix_shift_for(user, shift_name):
    double_print('Fixing Work Shift for', user.full_name, 'with shift', shift_name)
    doj = user.detail.joined_date
    shift_base = WorkShift.objects.filter()
    organization = user.detail.organization
    if not organization:
        double_print('No Organization found in user detail.')
        return
    shift_qs = shift_base.filter(
        organization=user.detail.organization
    ).filter(
        name=shift_name
    )
    try:
        shift = shift_qs.get()
    except:
        double_print('No shift with given name', shift_name, 'was found')
        return
    user_shift_qs = IndividualUserShift.objects.filter(
        individual_setting__user=user
    )
    first_shift = user_shift_qs.filter(
        applicable_from__lte=doj
    ).order_by(
        '-applicable_from'
    ).first()
    if first_shift:
        double_print('Shift found at doj', first_shift)
    starting_shift = user_shift_qs.order_by(
        'applicable_from'
    ).first()
    if not starting_shift:
        terminal_date = user.detail.resigned_date
        double_print('No shift found')
    else:
        terminal_date = starting_shift.applicable_from - timezone.timedelta(days=1)
    setting = user.attendance_setting
    if not setting:
        double_print('No Attendance Setting was found.')
        setting = IndividualAttendanceSetting.objects.create(user=user)
    double_print(
        'Create Individual Shift',
        shift,
        'from',
        doj,
        'to',
        terminal_date
    )
    IndividualUserShift.objects.create(
        shift=shift,
        individual_setting=setting,
        applicable_from=doj,
        applicable_to=terminal_date
    )


def build_timesheet_for(user, doj_given, shift_name):
    double_print('Building TimeSheet for ', user.full_name)
    for _date in daily_iterator(
            user.detail.joined_date,
            user.detail.resigned_date or get_today()
    ):
        (
            timesheets, created_count, updated_count, status
        ) = TimeSheet.objects._create_or_update_timesheet_for_profile(
            user=user,
            date_=_date
        )
        double_print('\rTime Sheet creation for', _date, status, end='')
    double_print()


def main():
    for dat in current_employee_data:
        double_print()
        double_print('=' * 10)
        email = dat.get('email')
        double_print('Processing', email)
        doj_given = dat.get('doj')
        try:
            user = USER.objects.get(email=email)
        except:
            double_print('User was not found')
            continue
        shift_name = dat.get('shift_name')
        fix_shift_for(user, shift_name)
        build_timesheet_for(user, doj_given, shift_name)

    try:
        past_employee = USER.objects.get(
            first_name='Rajendra',
            last_name='Karki'
        )
    except:
        double_print('User not found for Rajendra Karki')
        return
    # Fixing mess
    # Read-Only Script created timesheet for past user for today.
    TimeSheet.objects.filter(
        timesheet_user=past_employee,
        timesheet_for='2020-03-25'
    ).delete()
    fix_shift_for(past_employee, 'Standard Working Time')
    build_timesheet_for(past_employee, '11/3/2019', 'Standard Working Time')


with transaction.atomic():
    main()
