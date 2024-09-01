from rest_framework import serializers
from .models import InstitutionStatsByType, Institution, TypeInstitution, SocialNetwork

class TypeInstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeInstitution
        fields = ['id', 'name']

class SocialNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialNetwork
        fields = ['id', 'name']

class InstitutionStatsByTypeSerializer(serializers.ModelSerializer):
    type_institution = TypeInstitutionSerializer(read_only=True)
    social_network = SocialNetworkSerializer(read_only=True)

    class Meta:
        model = InstitutionStatsByType
        fields = ['id', 'type_institution', 'social_network', 'stats_date', 'total_followers',
                  'total_publications', 'total_reactions', 'average_views', 'institution_count', 'date_updated']

class InstitutionSerializer(serializers.ModelSerializer):
    type_institution = TypeInstitutionSerializer(read_only=True)

    class Meta:
        model = Institution
        fields = ['id', 'name', 'city', 'type_institution']