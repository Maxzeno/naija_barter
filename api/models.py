from datetime import timedelta
import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from api.utils.helpers import validate_alphanumeric_password

# Create your models here.


class BaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_unique_id(self):
        allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        unique_id = get_random_string(length=6, allowed_chars=allowed_chars)
        while self.__class__.objects.filter(id=unique_id).exists():
            unique_id = get_random_string(
                length=6, allowed_chars=allowed_chars)
        return unique_id

    class Meta:
        abstract = True


class MyUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValidationError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, password=password, **extra_fields)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValidationError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValidationError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    id = models.CharField(primary_key=True, max_length=6, editable=False)
    image = models.ImageField(upload_to='images/user/', blank=True, null=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=250)
    phone = models.CharField(max_length=25)
    username = models.CharField(max_length=250)
    dob = models.DateField(blank=True, null=True)
    location = models.CharField(
        max_length=250, blank=True, null=True)  # required for business
    business_name = models.CharField(
        max_length=250, blank=True, null=True)  # required for business
    regitration_no = models.CharField(
        max_length=100, blank=True, null=True)  # required for business
    is_business = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    email_confirmed = models.BooleanField(default=False)
    otp_tries = models.IntegerField(default=0)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry_date = models.DateTimeField(null=True, blank=True)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.generate_unique_id()

        if self.is_business:
            if not self.business_name or not self.regitration_no or not self.location:
                raise ValidationError(
                    'Business most have business name, regitration no. and location')

        user = self.__class__.objects.filter(id=self.id).first()
        if not user or user and user.password != self.password:
            if len(self.password) < 8 or validate_alphanumeric_password(self.password):
                raise ValidationError(
                    'Password most be alpha numeric and greater than 8 characters')
            self.set_password(self.password)

        if user and not self.is_staff and self.is_superuser:
            self.is_staff = True

        super().save(*args, **kwargs)

    def generate_otp(self, length=4, hours=24):
        characters = '0123456789'
        otp = ''.join(random.choice(characters) for _ in range(length))
        self.otp = otp
        self.otp_tries = 0
        self.otp_expiry_date = timezone.now() + timedelta(hours=hours)
        self.save()
        return self.otp

    def verify_otp(self, otp):
        origin_otp = self.otp
        origin_otp_expiry_date = self.otp_expiry_date
        self.otp_tries = self.otp_tries + 1
        self.save()

        if self.otp_tries-1 > 5:
            return False

        if not otp or not origin_otp or not origin_otp_expiry_date:
            return False

        return timezone.now() < origin_otp_expiry_date and origin_otp == otp

    def clear_otp(self):
        self.otp = None
        self.otp_tries = 0
        self.otp_expiry_date = None
        self.save()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return f'{self.email} {self.username}'


class Location(BaseModel):
    state = models.CharField(max_length=250, unique=True)


class Category(BaseModel):
    name = models.CharField(max_length=250, unique=True)
    description = models.TextField(max_length=1000, blank=True, null=True)


class Product(BaseModel):
    PRODUCT_CHOICES = [
        ('barter', 'Barter'),
        ('declutter', 'Declutter'),
        ('gift', 'Gift'),
    ]

    id = models.CharField(primary_key=True, max_length=6, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='images/product/', blank=True, null=True)
    name = models.CharField(max_length=250)
    description = models.TextField(max_length=1000)
    is_active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=20, decimal_places=0, default=0, validators=[
                                MinValueValidator(0, "Price should not be less than zero")])
    exchange = models.CharField(max_length=250, blank=True, null=True)
    product_type = models.CharField(max_length=10, choices=PRODUCT_CHOICES)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.generate_unique_id()

        if self.product_type == 'barter':
            if not self.exchange:
                raise ValidationError(
                    "Product type barter most have an exchange")

        if self.product_type == 'gift':
            if self.price != 0:
                raise ValidationError(
                    "Product type gift most have price of zero")
