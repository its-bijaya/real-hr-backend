from irhrs.notification.models import Notification

changes = [
    ('/user/attendance/claim-overtime', '/user/attendance/request/overtime-claims'),
    ('/user/attendance/overtime-claims', '/user/attendance/reports/overtime-claims'),
    ('/user/supervisor/attendance/overtime-claim-requests', '/user/supervisor/attendance/requests/overtime-claims'),
    ('/user/attendance/adjustment', '/user/attendance/reports/adjustment'),
    ('/user/supervisor/attendance-adjustments', '/user/supervisor/attendance/requests/adjustments'),
    ('/user/leave/leave-request', '/user/leave/request'),
    ('/user/supervisor/leave-requests', '/user/supervisor/leave/requests'),
    ('/user/activities/my-change-requests', '/user/profile/change-request'),
]

# ones that need some extra effort
exceptionals = [
    (('/user/task/my/', '/approval-detail'), ('/user/task/approvals/', '/detail')),
    (('/organization/', '/hris/change-requests'), ('/admin/', '/hris/change-requests'))
]


def main():
    for old_url, new_url in changes:
        Notification.objects.filter(url=old_url).update(url=new_url)

    # fixing exceptionals
    for old_url, new_url in exceptionals:
        # luckily both have 3 parts
        starts_with = old_url[0]
        ends_with = old_url[1]
        new_starts_with = new_url[0]
        new_ends_with = new_url[1]

        applicable_notifications = Notification.objects.filter(url__startswith=starts_with, url__endswith=ends_with)

        for notification in applicable_notifications:
            notification_url = notification.url
            notification.url = notification_url.replace(starts_with, new_starts_with).replace(ends_with, new_ends_with)
            notification.save(update_fields=['url'])
            print(f"Changed `{notification_url}` to `{notification.url}`")


if __name__ == "__main__":
    main()
