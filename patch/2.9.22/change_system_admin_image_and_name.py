
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.auth import get_user_model

User = get_user_model()

bot = User.objects.get(email='info@realhrsoft.com')
bot_image = staticfiles_storage.open('logos/laxmi-bank-bot-logo.jpg')
bot.first_name = 'Laxmi'
bot.last_name = 'Bank'
bot.profile_picture = bot_image
bot.save()
bot_image.close()
