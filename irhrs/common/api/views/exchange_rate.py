from dateutil.parser import parse as dateparse
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from irhrs.common.api.permission import CommonExchangeRatePermission
from irhrs.common.api.serializers.exchange_rate import ExchangeRateSerializer
from irhrs.common.models.exchange_rate import ExchangeRate
from irhrs.core.utils.common import get_today


class ExchangeRateViewSet(ModelViewSet):
    """
    Currency Exchange rate

    sample post data

        {
            "from_amount": 1
            "from_currency": "USD",
            "to_amount": 120,
            "to_currency": "NRS",
            "from_date": "2020-01-01",
            "to_date": "2020-03-01"
        }

    to get list of active rates
    `/api/v1/commons/exchange-rates/active-rates`

    to get active rate for a date
    `/api/v1/commons/exchange-rates/active-rates?effective_date=2020-01-01`
    """
    queryset = ExchangeRate.objects.all()
    serializer_class = ExchangeRateSerializer
    permission_classes = [CommonExchangeRatePermission]
    filter_backends = [OrderingFilter]
    ordering_fields = [
        'from_date',
        'to_date',
        'created_at',
        'modified_at'
    ]

    @action(detail=False, methods=['GET'], url_path='active-rates')
    def active_rates(self, request, *args, **kwargs):

        effective_date_str = self.request.query_params.get('effective_date')
        if effective_date_str:
            try:
                effective_date = dateparse(effective_date_str)
            except(TypeError, ValueError):
                raise ValidationError({'effective_date': ['Invalid effective_date sent.']})
        else:
            effective_date = get_today()

        qs = self.get_queryset().filter(
            from_date__lte=effective_date, to_date__gte=effective_date
        )
        self.queryset = qs
        return super().list(request, *args, **kwargs)
