from django.db import models

class Institution(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    type = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class SocialNetwork(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class CollectionDate(models.Model):
    date = models.DateField()
    name_period = models.CharField(max_length=50)

    def __str__(self):
        return self.name_period

class BaseMetrics(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    socialnetwork = models.ForeignKey(SocialNetwork, on_delete=models.CASCADE)
    collectiondate = models.ForeignKey(CollectionDate, on_delete=models.CASCADE)
    followers = models.IntegerField()
    publications = models.IntegerField()
    likes = models.IntegerField()

class CalculateMetrics(models.Model):
    metrics_base = models.OneToOneField(BaseMetrics, on_delete=models.CASCADE)
    engagement_rate = models.FloatField()