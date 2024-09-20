from irhrs.core.mixins.viewset_mixins import PastUserParamMixin


class LeaveRequestPastUserFilterMixin(PastUserParamMixin):
    def get_queryset(self):
        qs = super().get_queryset().filter(
            user__user_experiences__isnull=False
        )
        if self.user_type == 'active':
            qs = qs.filter(
                user__user_experiences__isnull=True
            )
        elif self.user_type == 'past':
            qs = qs.exclude(
                user__user_experiences__isnull=True
            )
        return qs.distinct()
