import os

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


ALLOWED_IMAGES = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_VIDEOS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}


def validate_media_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_IMAGES | ALLOWED_VIDEOS:
        raise ValidationError(
            f'Formato no permitido. Usa imagenes ({", ".join(sorted(ALLOWED_IMAGES))}) '
            f'o videos ({", ".join(sorted(ALLOWED_VIDEOS))}).'
        )
    max_size_mb = 20
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'El archivo supera {max_size_mb}MB.')


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def cover_media(self):
        return self.media.order_by('position', 'id').first()

    def next_media_position(self):
        max_position = self.media.aggregate(max_pos=Max('position'))['max_pos'] or 0
        return max_position + 1

    def normalize_media_positions(self):
        """Compacta posiciones para evitar duplicados tras ediciones/eliminaciones."""
        for index, media in enumerate(self.media.order_by('position', 'id'), start=1):
            if media.position != index:
                media.position = index
                media.save(update_fields=['position'])


class ProductMedia(models.Model):
    IMAGE = 'image'
    VIDEO = 'video'
    MEDIA_TYPES = [
        (IMAGE, 'Imagen'),
        (VIDEO, 'Video'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='products/media/', validators=[validate_media_file])
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('position', 'id')
        unique_together = ('product', 'position')

    def __str__(self):
        return f'{self.product.name} - {self.media_type}'

    @staticmethod
    def detect_media_type(filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext in ALLOWED_IMAGES:
            return ProductMedia.IMAGE
        if ext in ALLOWED_VIDEOS:
            return ProductMedia.VIDEO
        raise ValidationError('Tipo de archivo no soportado.')

    def save(self, *args, **kwargs):
        if not self.media_type:
            self.media_type = self.detect_media_type(self.file.name)
        if self.position == 0 and self.product_id:
            self.position = self.product.next_media_position()
        super().save(*args, **kwargs)
