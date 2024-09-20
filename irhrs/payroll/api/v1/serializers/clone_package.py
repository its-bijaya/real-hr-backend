from django.db import transaction
from rest_framework import serializers

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.utils.common import DummyObject
from irhrs.payroll.api.v1.serializers import PackageSerializer
from irhrs.payroll.models import Package, CLONED_PACKAGE
from irhrs.payroll.tasks import create_package_activity
from irhrs.payroll.utils.package_clone import clone_package_from_another_package


class PackageCloneSerializer(DummySerializer):
    old_package = serializers.PrimaryKeyRelatedField(
        queryset=Package.objects.all(),
        write_only=True
    )
    new_package_name = serializers.CharField(
        max_length=150,
        write_only=True
    )
    new_package = PackageSerializer(read_only=True)

    def validate_old_package(self, old_package):
        if old_package.organization != self.context.get("organization"):
            raise serializers.ValidationError("Old package not found for this organization.")
        return old_package

    def validate_new_package_name(self, package_name):
        organization = self.context.get('organization')
        if Package.objects.filter(
            organization=organization, name=package_name
        ).exists():
            raise serializers.ValidationError("Package with this name already"
                                              " exists for this organization.")

        return package_name

    def create(self, validated_data):
        old_package = validated_data.get('old_package')
        new_package_name = validated_data.get('new_package_name')

        user = self.context.get('request').user
        with transaction.atomic():
            new_package = clone_package_from_another_package(old_package, new_package_name, actor=user, action=CLONED_PACKAGE, bulk=False)
        title = f'{user.full_name} has {CLONED_PACKAGE} a package named "{old_package.name}" to "{new_package_name}"'
        create_package_activity(title=title, package=old_package, action=CLONED_PACKAGE)
        return DummyObject(new_package=new_package)
