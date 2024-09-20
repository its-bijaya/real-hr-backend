from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from irhrs.appraisal.constants import INDIVIDUAL_KPI_COLLECTION_STATUS, PENDING, ACKNOWLEDGED
from irhrs.common.models import BaseModel
from django.db import models

from irhrs.organization.models import Organization, EmploymentJobTitle, OrganizationDivision, \
    EmploymentLevel, FiscalYear
from irhrs.users.models import User


class KPI(BaseModel):
    title = models.CharField(max_length=255)
    success_criteria = models.TextField()
    organization = models.ForeignKey(
        Organization,
        related_name='kpi_collections',
        on_delete=models.CASCADE
    )
    job_title = models.ManyToManyField(
        EmploymentJobTitle,
        related_name='kpi_collections',
    )
    division = models.ManyToManyField(
        OrganizationDivision,
        related_name='kpi_collections',
        blank=True,
    )
    employment_level = models.ManyToManyField(
        EmploymentLevel,
        related_name='kpi_collections',
        blank=True
    )
    is_archived = models.BooleanField(default=False)

    class Meta:
        unique_together = (('organization', 'title'),)
        ordering = ('-created_at',)

    def __str__(self):
        return self.title


class IndividualKPI(BaseModel):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(
        User,
        related_name='individual_kpis',
        on_delete=models.CASCADE
    )
    fiscal_year = models.ForeignKey(
        FiscalYear,
        related_name='individual_kpis',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        choices=INDIVIDUAL_KPI_COLLECTION_STATUS,
        max_length=15,
        default=PENDING
    )
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.title


class ExtendedIndividualKPI(BaseModel):
    individual_kpi = models.ForeignKey(
        IndividualKPI,
        related_name='extended_individual_kpis',
        on_delete=models.CASCADE
    )
    kpi = models.ForeignKey(
        KPI,
        related_name='extended_individual_kpis',
        on_delete=models.PROTECT
    )
    success_criteria = models.TextField()
    weightage = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )

    def __str__(self):
        return f"{self.individual_kpi.title}"

    def save(self, *args, **kwargs):
        if self.individual_kpi.status == ACKNOWLEDGED:
            raise ValidationError({"error": "Can not update Acknowledged KPI."})
        super().save(*args, **kwargs)


class IndividualKPIHistory(BaseModel):
    individual_kpi = models.ForeignKey(
        IndividualKPI,
        related_name='histories',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        choices=INDIVIDUAL_KPI_COLLECTION_STATUS,
        max_length=15,
        default=PENDING
    )
    remarks = models.TextField(max_length=600, blank=True, null=True)

    def __str__(self):
        return f"{self.individual_kpi.user}"


