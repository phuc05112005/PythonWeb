from django.db import models


class Store(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    district = models.CharField(max_length=100)
    lat = models.FloatField()
    lng = models.FloatField()

    def __str__(self):
        return self.name
