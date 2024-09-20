import os, requests

from django.contrib.auth import get_user_model

BASE_LINK = "http://127.0.0.1:8000/media/"

User = get_user_model()


def main():
    current_directory = os.getcwd()
    main_folder = os.path.join(current_directory, r'laxmisunrise')
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)

    for user in User.objects.all().current().only('email', 'username', 'profile_picture', 'signature'):
        os.chdir(main_folder)
        user_username = user.username
        profile_picture = user.profile_picture
        if profile_picture:
            profile_picture = BASE_LINK + str(profile_picture)
            img_bytes = requests.get(profile_picture).content
            with open(user_username, 'wb') as img_file:
                img_file.write(img_bytes)
                print(f'{user_username} was downloaded...')


if __name__ == '__main__':
    main()
