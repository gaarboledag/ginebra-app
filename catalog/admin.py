from django.contrib import admin
from .models import Category, Product, ProductMedia


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 0
    fields = ('file', 'media_type', 'position', 'created_at')
    readonly_fields = ('media_type', 'created_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at', 'updated_at')
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    autocomplete_fields = ('category',)
    inlines = (ProductMediaInline,)

# Register your models here.
