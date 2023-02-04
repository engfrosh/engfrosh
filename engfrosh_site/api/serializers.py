from rest_framework import serializers
import common_models.models as md


class VerificationPhotoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = md.VerificationPhoto
        fields = ['photo']
