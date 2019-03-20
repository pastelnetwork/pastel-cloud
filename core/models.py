from django.contrib.auth.models import AbstractUser
from django.db import models


# Custom User model to simplify adding new field in future
class User(AbstractUser):
    def save(self, *args, **kwargs):
        is_new = self.id is None
        super(User, self).save(*args, **kwargs)
        if is_new:
            self.profile = UserProfile.objects.create(user=self)


class Address(models.Model):
    country = models.CharField(max_length=64, null=True, blank=True)
    state = models.CharField(max_length=64, null=True, blank=True)
    city = models.CharField(max_length=64, null=True, blank=True)
    street = models.CharField(max_length=64, null=True, blank=True)
    postal_code = models.CharField(max_length=64, null=True, blank=True)
    number = models.CharField(max_length=64, null=True, blank=True)


class UserProfile(models.Model):
    short_bio = models.TextField(blank=True)
    picture = models.TextField(null=True, blank=True, db_index=False)  # base64 image
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=32, null=True, blank=True)
    billing_address = models.OneToOneField(Address, null=True, blank=True, on_delete=models.SET_NULL,
                                           related_name='profile')

    @property
    def first_name(self):
        return self.user.first_name

    @first_name.setter
    def first_name(self, value):
        self.user.first_name = value

    @property
    def last_name(self):
        return self.user.last_name

    @last_name.setter
    def last_name(self, value):
        self.user.last_name = value

    @property
    def email(self):
        return self.user.email

    @property
    def date_joined(self):
        return self.user.date_joined

    def __str__(self):
        return '{} profile'.format(self.user.username)
