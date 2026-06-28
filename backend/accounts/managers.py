from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """email をログイン識別子とするカスタムユーザーマネージャー。"""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("email は必須です")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "owner")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("superuser は is_staff=True が必要です")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("superuser は is_superuser=True が必要です")
        return self._create_user(email, password, **extra_fields)
