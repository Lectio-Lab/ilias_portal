from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class IliasCredential(models.Model):
    """
    Per-user ILIAS session state.

    University passwords are never persisted. Authentication is interactive
    browser MFA; only session cookies (phpsessid / shibsession) are stored.
    ``ilias_username`` may optionally be kept as a display hint.
    ``ilias_password`` remains as an empty legacy column and must stay blank.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="ilias_credential"
    )
    ilias_username = models.TextField(blank=True, default="")
    ilias_password = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Deprecated. University passwords are never persisted; "
            "auth uses interactive browser MFA and session cookies only."
        ),
    )
    phpsessid = models.TextField(blank=True, null=True)
    shibsession = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_iliascredential"
        verbose_name = "ILIAS credential"
        verbose_name_plural = "ILIAS credentials"

    def __str__(self):
        return f"IliasCredential({self.user.email})"
