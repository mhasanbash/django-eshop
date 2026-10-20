from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ('email',)
        
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'phone_number', 'score')
        
class UserUpdateSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'address', 'postal_code', 'province', 'city')
        

        