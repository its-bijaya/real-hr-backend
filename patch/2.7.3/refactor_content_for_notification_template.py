template_content = None


def take_backup(apps, scheme):
    global template_content
    NotificationTemplate = apps.get_model('common', 'NotificationTemplate')
    template_content = NotificationTemplate.objects.all()


def set_data(apps, scheme):
    global template_content
    NotificationTemplateContent = apps.get_model('common', 'NotificationTemplateContent')
    updated_id = []
    new_content = []
    for datum in template_content:
        updated_id.append(datum.id)
        new_content.append(
            NotificationTemplateContent(
                template_id=datum.id,
                content=datum.content
            )
        )
    if new_content:
        NotificationTemplateContent.objects.bulk_create(new_content)
    if updated_id:
        print(f'Updated data are: ')
        print(updated_id)
