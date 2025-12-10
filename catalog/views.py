from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)

from .forms import (
    CategoryForm,
    ProductForm,
    ProductMediaFormSet,
    ProductMediaUploadForm,
)
from .models import Category, Product, ProductMedia


def login_view(request):
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('product_list')
        messages.error(request, 'Credenciales inválidas, intenta nuevamente.')

    return render(request, 'catalog/login.html')


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    queryset = Product.objects.select_related('category').prefetch_related('media').order_by('-created_at')


class ProductMediaMixin:
    media_upload_form_class = ProductMediaUploadForm
    media_formset_class = ProductMediaFormSet

    def get_media_upload_form(self):
        if self.request.method in ('POST', 'PUT'):
            return self.media_upload_form_class(self.request.POST, self.request.FILES)
        return self.media_upload_form_class()

    def get_media_formset(self):
        if not getattr(self, 'object', None):
            return None
        if self.request.method in ('POST', 'PUT'):
            return self.media_formset_class(self.request.POST, self.request.FILES, instance=self.object)
        return self.media_formset_class(instance=self.object)

    def save_uploaded_media(self, product, files):
        if not files:
            return
        new_media = []
        current_position = product.next_media_position() - 1
        for idx, file in enumerate(files, start=1):
            media_type = ProductMedia.detect_media_type(file.name)
            new_media.append(
                ProductMedia(
                    product=product,
                    file=file,
                    media_type=media_type,
                    position=current_position + idx,
                )
            )
        ProductMedia.objects.bulk_create(new_media)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('media_upload_form', getattr(self, 'media_upload_form', self.get_media_upload_form()))
        if getattr(self, 'object', None):
            context.setdefault('media_formset', getattr(self, 'media_formset', self.get_media_formset()))
        return context


class ProductCreateView(LoginRequiredMixin, ProductMediaMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('media_formset', None)
        return context

    def form_valid(self, form):
        self.media_upload_form = self.get_media_upload_form()
        if not self.media_upload_form.is_valid():
            return self.form_invalid(form)
        with transaction.atomic():
            self.object = form.save()
            self.save_uploaded_media(self.object, self.media_upload_form.cleaned_data.get('files'))
        messages.success(self.request, 'Producto creado correctamente.')
        return redirect(self.get_success_url())


class ProductUpdateView(LoginRequiredMixin, ProductMediaMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        self.media_upload_form = self.get_media_upload_form()
        self.media_formset = self.get_media_formset()
        if not self.media_upload_form.is_valid() or not self.media_formset.is_valid():
            return self.form_invalid(form)
        with transaction.atomic():
            self.object = form.save()
            self.media_formset.instance = self.object
            self.media_formset.save()
            self.save_uploaded_media(self.object, self.media_upload_form.cleaned_data.get('files'))
            self.object.normalize_media_positions()
        messages.success(self.request, 'Producto actualizado correctamente.')
        return redirect(self.get_success_url())


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('product_list')


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'catalog/category_list.html'
    context_object_name = 'categories'
    queryset = Category.objects.order_by('name')


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category_form.html'
    success_url = reverse_lazy('category_list')


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'catalog/category_form.html'
    success_url = reverse_lazy('category_list')


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'catalog/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'No puedes eliminar la categoría porque tiene productos asociados.')
            return redirect(self.success_url)
