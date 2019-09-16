import json
import base64
import base58
import hashlib
from collections import OrderedDict

from ecpy.keys import ECPublicKey
from rest_framework import serializers
from rest_framework.generics import RetrieveUpdateAPIView

from core.models import UserProfile, Address, PastelIDProfile

from ecpy.eddsa import EDDSA
from ecpy.curves import Curve


def restore_bytes_from_base64_string(pk_string):
    bytes_encoded = pk_string.encode()
    return base64.b64decode(bytes_encoded)

def restore_public_key_from_pastel_id(pk_string):
    bytes_encoded = pk_string.encode()
    decoded = base58.b58decode(bytes_encoded)
    # cut first two bytes which are always {0xA1,0xDE}, and 4 last bytes which are hash of the key.
    return decoded[2:][:-4]


def ordered_json_string_from_dict(data):
    sorted_data = sorted(data.items(), key=lambda x: x[0])
    ordered = OrderedDict(sorted_data)
    return json.dumps(ordered)


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
    picture_hash = serializers.CharField(write_only=True)

    class Meta:
        model = PastelIDProfile
        fields = ('pastel_id', 'picture', 'first_name', 'last_name',
                  'email', 'phone_number', 'date_joined_for_human', 'signature', 'picture_hash')

    def validate(self, data):

        # TODO: 1. check signature of JSON text instead of bytes
        # TODO: 2. restore pastelID from base 58,
        # TODO: 3. restore signature from base 64
        # TODO: 4. Use ECpy to verify signature
        data = super(PastelProfileSerializer, self).validate(data)
        signature = data.pop('signature')
        pastel_id = data.pop('pastel_id')
        picture = None
        if 'picture' in data:
            picture = data.pop('picture')
            picture_hash = data.get('picture_hash')
            if not picture_hash:
                raise serializers.ValidationError("'picture' field included but 'picture_hash' is absent")
            if picture_hash != hashlib.md5(picture.encode('utf-8')).hexdigest():
                raise serializers.ValidationError("Picture hash is incorrect")
        signed_text_data = ordered_json_string_from_dict(data)
        signed_text_data_bytes = signed_text_data.encode()
        signature_bytes = restore_bytes_from_base64_string(signature)
        public_key_bytes = restore_public_key_from_pastel_id(pastel_id)

        #
        # ed_521 = get_Ed521() # use ecpy
        # signature_valid = ed_521.verify(public_key_bytes, signed_text_data, signature_bytes) # use ecpy
        # curve = Curve.get_curve('Ed448')
        # point = curve.decode_point(public_key_bytes)
        # ec_pub_key = ECPublicKey(point)
        #
        # signer = EDDSA(hashlib.shake_256, hash_len=114)
        # signature_valid = signer.verify(signed_text_data_bytes, signature_bytes, ec_pub_key)

        # FIXME: currently signature is not verified (however it's send on the client side
        # For some reason ECPY does not provide convinient way to verify signature with public key, while
        # attempt to regenerate ECPublicKey instance from public key bytes leads to failing verification
        # of the signature.
        # Suggested way of implementing signature verification is to extract appropriate code from cNode (aka pasteld)
        # compile it as small module and use from python (or even better - create python bindings).
        signature_valid = True
        if not signature_valid:
            raise serializers.ValidationError("Signature is invalid")
        # Now when validation is complete we put picture back on its place
        if picture:
            data['picture'] = picture
        return data


class PastelProfileView(RetrieveUpdateAPIView):
    """
    A trick for transporting pastel public key in request data:
    POST is used to fetch profile,
    PUT/PATCH - to update it.
    """
    serializer_class = PastelProfileSerializer
    # permission_classes = (IsAuthenticated,)

    def get_object(self):
        pastel_id = self.request.data.get('pastel_id')

        pastel_id_profile, _ = PastelIDProfile.objects.get_or_create(pastel_id=pastel_id)
        return pastel_id_profile

    def get(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
