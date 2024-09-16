from django.db import models

class TypeInstitution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(max_length=255, blank=True, null=True)
    ordering = models.IntegerField(null=True, blank=True)
    institution_count = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return self.name
    
class SocialNetwork(models.Model):
    name = models.CharField(max_length=50, unique=True)
    percentage_correction_type_institutions = models.IntegerField(null=True, blank=True, default=0)
    percentage_correction_social_networks = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return self.name
    
class InstitutionStatsByType(models.Model):

    type_institution = models.ForeignKey(TypeInstitution, on_delete=models.CASCADE)
    social_network = models.ForeignKey(SocialNetwork, on_delete=models.CASCADE)
    total_followers = models.BigIntegerField(null=True, blank=True, default=0)
    total_publications = models.BigIntegerField(null=True, blank=True, default=0)
    total_reactions = models.BigIntegerField(null=True, blank=True, default=0)
    average_views = models.FloatField(null=True, blank=True, default=0.0)
    stats_date = models.DateField()
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('type_institution', 'social_network', 'stats_date')

    def __str__(self):
        return f"{self.type_institution.name} - {self.social_network.name} Stats ({self.stats_date})"

class Institution(models.Model):
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=100)
    type_institution = models.ForeignKey(TypeInstitution, on_delete=models.CASCADE)

    def __str__(self):
        return self.name 

class BaseMetrics(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    socialnetwork = models.ForeignKey(SocialNetwork, on_delete=models.CASCADE)

    # collectiondate = models.ForeignKey(CollectionDate, on_delete=models.CASCADE)
    followers = models.BigIntegerField()
    publications = models.BigIntegerField()
    reactions = models.BigIntegerField()
    date_collection = models.DateField(blank=True, null=True)
    Average_views = models.FloatField(blank=True, null=True)

