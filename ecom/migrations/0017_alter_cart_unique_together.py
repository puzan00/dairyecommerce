# Generated by Django 5.1.5 on 2025-02-02 14:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0016_cart'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cart',
            unique_together={('customer', 'product')},
        ),
    ]
