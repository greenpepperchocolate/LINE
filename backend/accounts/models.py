import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    email + パスワードでログインするカスタムユーザー。
    role は管理画面のスタッフ権限 (owner/admin/staff) を表す。
    """

    ROLE_CHOICES = (
        ("owner", "owner"),
        ("admin", "admin"),
        ("staff", "staff"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120, blank=True, default="")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="owner")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
