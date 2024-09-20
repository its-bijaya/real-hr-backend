# This file should not be compiled
from django.core.cache import cache

from irhrs.payroll.models import UserExperiencePackageSlot
from irhrs.payroll.utils.backdated_calculations import update_or_create_backdated_payroll
from irhrs.payroll.utils.calculator import create_package_rows


def sync_create_package_rows(_pk, cache_key, key):
    active_key = cache.get(cache_key)
    if active_key == key or active_key is None:
        # process only if
        # requested package_update is the latest one (from cache)
        # or no active key is present (usually after restart or some other scenario)
        #
        # This will help to remove multiple package wise salary generation for (quick) edits in
        # package
        instance = UserExperiencePackageSlot.objects.get(id=_pk)
        create_package_rows(instance)
        cache.delete(cache_key)


def sync_update_backdated_payroll(slot_id):
    slot = UserExperiencePackageSlot.objects.get(id=slot_id)
    update_or_create_backdated_payroll(slot)
