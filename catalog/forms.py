from django import forms
from django.forms import inlineformset_factory

from .models import Category, Product, ProductMedia


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'slug': forms.TextInput(attrs={'class': 'input'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'description': forms.Textarea(attrs={'class': 'textarea', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'select'}),
            'price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
        }


class ProductMediaUploadForm(forms.Form):
    files = forms.FileField(
        label='Agregar imágenes o videos',
        widget=MultiFileInput(attrs={'multiple': True, 'class': 'input'}),
        required=False,
    )

    def clean_files(self):
        uploaded_files = self.files.getlist('files')
        for file_obj in uploaded_files:
            ProductMedia.file.field.run_validators(file_obj)
        return uploaded_files


ProductMediaFormSet = inlineformset_factory(
    Product,
    ProductMedia,
    fields=('position',),
    extra=0,
    can_delete=True,
    widgets={
        'position': forms.NumberInput(attrs={'class': 'input', 'min': 1}),
    },
)
