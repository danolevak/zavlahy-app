from rest_framework import serializers
from .models import Field


class FieldSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(source="crop.name", read_only=True)

    class Meta:
        model = Field
        fields = [
            "id",
            "name",
            "latitude",
            "longitude",
            "crop_id",
            "crop_name",
            "soil_type_id",
            "sowing_date",
        ]