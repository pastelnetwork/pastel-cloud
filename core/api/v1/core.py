from rest_framework import serializers
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from core.models import UserProfile, Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        exclude = ('id',)


class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    email = serializers.CharField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    billing_address = AddressSerializer()

    class Meta:
        model = UserProfile
        fields = ('short_bio', 'picture', 'first_name', 'last_name',
                  'email', 'phone_number', 'date_joined', 'billing_address')

    def update(self, instance, validated_data):
        billing_address = validated_data.pop('billing_address', None)
        instance = super(UserProfileSerializer, self).update(instance, validated_data)
        # save user. fields are set with @propety.setters in model, but not save to avoid several save() calls.
        instance.user.save()
        if billing_address:
            if instance.billing_address:
                for field in billing_address:
                    setattr(instance.billing_address, field, billing_address[field])

                instance.billing_address.save()
            else:
                instance.billing_address = Address.objects.create(**billing_address)
                instance.save()
        return instance


class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)
