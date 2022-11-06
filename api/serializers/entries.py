from rest_framework import serializers
from api.models import Entries

class EntriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entries
        fields = '__all__'