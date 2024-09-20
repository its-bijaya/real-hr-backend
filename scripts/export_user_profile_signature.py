from django.contrib.auth import get_user_model
from openpyxl import Workbook


wb = Workbook()

ws = wb.active

HEADERS =["Employee Name", "Username", "Email", "Profile Picture", "Signature"]
BASE_LINK = "http://127.0.0.1:8000/media/"

User = get_user_model()


def main():
    ws.append(HEADERS)
    for user in User.objects.all().current().only('email', 'username', 'profile_picture', 'signature'):
        profile_picture = str(user.profile_picture)
        signature = str(user.signature)
        if profile_picture:
            profile_picture = BASE_LINK+profile_picture
        if signature:
            signature = BASE_LINK + signature
        ws.append([user.full_name, user.username, user.email, profile_picture, signature])
    
    wb.save(f'user_export.xlsx')


if __name__ == '__main__':
    main()
