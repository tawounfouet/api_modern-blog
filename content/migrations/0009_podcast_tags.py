# Generated by Django 4.2.11 on 2025-06-14 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0008_post_meta_description_post_meta_title_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='podcast',
            name='tags',
            field=models.TextField(blank=True, help_text='Liste de tags séparés par des virgules pour le référencement'),
        ),
    ]
