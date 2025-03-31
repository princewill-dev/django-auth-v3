from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
import uuid
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Use set_password() to hash the password
        
        # Only set is_active=False if not explicitly provided
        if 'is_active' not in extra_fields:
            user.is_active = False
            
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    account_id = models.CharField(max_length=10, unique=True, blank=True, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, null=True, blank=True)
    email_verification_code_created_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def set_email_verification_code(self, code):
        self.email_verification_code = code
        self.email_verification_code_created_at = timezone.now()
        self.save()

    def is_email_verification_code_valid(self):
        if not self.email_verification_code or not self.email_verification_code_created_at:
            return False
        return (timezone.now() - self.email_verification_code_created_at).total_seconds() < 600  # 10 minutes

class BlacklistedToken(models.Model):
    """Store tokens that have been blacklisted (logged out)"""
    token = models.CharField(max_length=500, unique=True)
    user = models.ForeignKey(User, related_name='blacklisted_tokens', on_delete=models.CASCADE)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-blacklisted_at']

    def __str__(self):
        return f"{self.user.email} - {self.blacklisted_at}"

@receiver(pre_save, sender=User)
def generate_account_id(sender, instance, **kwargs):
    if not instance.account_id:
        while True:
            account_id = str(uuid.uuid4()).replace('-', '')[:10].upper()
            if not User.objects.filter(account_id=account_id).exists():
                instance.account_id = account_id
                break