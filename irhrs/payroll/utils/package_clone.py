"""
Clone package utils
"""
from irhrs.payroll.api.v1.serializers import PackageSerializer, PackageHeadingSerializer
from irhrs.payroll.models import Package, CLONED_PACKAGE


def clone_package_from_another_package(package: Package, new_package_name: str, actor=None, action=None, bulk=True) -> Package:
    """
    Clone package from another package of same organization
    :param package: Package instance
    :param new_package_name: New package name
    :param actor: Package Cloner
    :return: new Package instance

    NOTE: Wrap this function in atomic block for consistency
    """
    package_details = PackageSerializer(package).data

    # ---------------- create package ---------------------------------------- #

    package_create_headings = ['is_template', 'organization']

    package_create_details = {
        key: value for (key, value) in package_details.items()
        if key in package_create_headings
    }
    package_create_details['name'] = new_package_name
    create_serializer = PackageSerializer(data=package_create_details, context={'actor': actor, 'action': CLONED_PACKAGE, 'bulk': bulk})
    create_serializer.is_valid(raise_exception=True)

    new_package = create_serializer.save()

    # ---------------- end create package ------------------------------------ #

    # --------------- create headings ---------------------------------------- #

    for heading_data in package_details.get('package_headings'):
        heading_data["package"] = new_package.id
        heading_serializer = PackageHeadingSerializer(data=heading_data)
        heading_serializer.is_valid(raise_exception=True)
        heading_serializer.save()
    # --------------- end create headings ---------------------------------------- #

    return new_package
