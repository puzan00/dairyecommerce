# Generated by Django 5.1.5 on 2025-02-14 11:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0029_product_is_sold'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='is_read',
        ),
        migrations.RemoveField(
            model_name='product',
            name='read_date',
        ),
    ]
