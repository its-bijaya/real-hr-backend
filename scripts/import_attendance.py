"""SCRIPT TO IMPORT ATTENDANCE

1. place import files inside root_dir (should be inside media directory)
2. Run this script / import and run main()
"""
import os
from irhrs.organization.models import Organization
from irhrs.core.utils import get_system_admin
from irhrs.attendance.api.v1.serializers.process_export import export_failed


root_dir = '/home/ubuntu/media/attendance-chunks/'
organization_slug = "laxmi-bank"


def main():
    organization = Organization.objects.get(slug=organization_slug)
    system_admin = get_system_admin()

    with os.scandir(root_dir) as it:
        files = sorted(
            (entry.name for entry in it if entry.name.endswith('xlsx')))

        for file_name in files:
            print(f"Trying sync for {file_name}")
            export_failed(os.path.join(root_dir, file_name),
                          system_admin, organization)


if __name__ == '__main__':
    main()
