from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_master_user(sender, **kwargs):
    User = get_user_model()
    username = 'master'
    password = 'Memo2001.'

    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password)
