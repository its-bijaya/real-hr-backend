from django.contrib.postgres.fields import ArrayField
from django.db import models

from irhrs.common.models import BaseModel


class AbstractLocationConstant(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    name_ne = models.CharField(max_length=255, blank=True)
    alternative_names = ArrayField(
        models.CharField(max_length=255, blank=True),
        blank=True
    )
    alternative_names_ne = ArrayField(
        models.CharField(max_length=255, blank=True),
        blank=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Country(BaseModel):
    name = models.CharField(max_length=150, db_index=True, unique=True)
    name_ne = models.CharField(max_length=150, blank=True)
    nationality = models.CharField(max_length=150, db_index=True, unique=True)
    nationality_ne = models.CharField(max_length=150, blank=True)
    denonym = ArrayField(
        models.CharField(max_length=150, blank=True),
        blank=True
    )
    adjectival = ArrayField(
        models.CharField(max_length=150, blank=True),
        blank=True
    )
    relevance = models.IntegerField(null=True)

    class Meta:
        ordering = ('relevance',)

    def __str__(self):
        return self.name


class Province(AbstractLocationConstant, BaseModel):
    country = models.ForeignKey(Country, on_delete=models.PROTECT)


class District(AbstractLocationConstant, BaseModel):
    province = models.ForeignKey(Province, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class City(AbstractLocationConstant, BaseModel):
    name = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=25)
    district = models.ForeignKey(District, on_delete=models.PROTECT,
                                 related_name='cities')
    district_name = models.CharField(blank=True, max_length=255)
    province = models.CharField(blank=True, max_length=255)
    country = models.CharField(blank=True, max_length=255)
    image = models.ImageField(upload_to='local-governments', blank=True)

    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    relevance = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        if not self.district_name:
            self.district_name = self.district.name
        if not self.province:
            self.province = self.district.province.name
        if not self.country:
            self.country = self.district.province.country.name
        super().save(*args, **kwargs)

    def __str__(self):
        full_location = '{}, {}, {}, {}'.format(
            self.name,
            self.district_name,
            self.province,
            self.country,
        )
        return full_location

    class Meta:
        unique_together = ('name', 'district')
