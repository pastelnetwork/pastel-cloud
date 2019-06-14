import json
import base64
from rest_framework import serializers
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from core.models import UserProfile, Address, PastelIDProfile
from blackblox_modules.crypto import get_Ed521


def restore_bytes_from_string(pk_string):
    bytes_encoded = pk_string.encode()
    return base64.b64decode(bytes_encoded)


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
    # permission_classes = (IsAuthenticated,)

    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)


class PastelProfileSerializer(serializers.ModelSerializer):
    signature = serializers.CharField(write_only=True)

    class Meta:
        model = PastelIDProfile
        fields = ('pastel_id', 'picture', 'first_name', 'last_name',
                  'email', 'phone_number', 'date_joined', 'signature')

    # def validate(self, data):
    #     data = super(PastelProfileSerializer, self).validate(data)
    #     signature = data.pop('signature')
    #     pastel_id = data.pop('pastel_id')
    #     raw_data = json.dumps(data).encode()
    #     signature_bytes = restore_bytes_from_string(signature)
    #     public_key_bytes = restore_bytes_from_string(pastel_id)
    #     ed_521 = get_Ed521()
    #     signature_valid = ed_521.verify(public_key_bytes, raw_data, signature_bytes)
    #     if not signature_valid:
    #         raise serializers.ValidationError("Signature is invalid")
    #     return data


class PastelProfileView(RetrieveUpdateAPIView):
    serializer_class = PastelProfileSerializer
    # permission_classes = (IsAuthenticated,)

    def get_object(self):
        if self.request.method == 'GET':
            pastel_id = self.request.GET.get('pastel_id')
        else:
            pastel_id = self.request.data.get('pastel_id')

        pastel_id_profile, _ = PastelIDProfile.objects.get_or_create(pastel_id=pastel_id)
        return pastel_id_profile

