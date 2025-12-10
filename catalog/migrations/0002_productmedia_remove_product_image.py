from django.db import migrations, models
import django.db.models.deletion
import catalog.models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='image',
        ),
        migrations.CreateModel(
            name='ProductMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='products/media/', validators=[catalog.models.validate_media_file])),
                ('media_type', models.CharField(blank=True, choices=[('image', 'Imagen'), ('video', 'Video')], max_length=10)),
                ('position', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', to='catalog.product')),
            ],
            options={
                'ordering': ('position', 'id'),
                'unique_together': {('product', 'position')},
            },
        ),
    ]
