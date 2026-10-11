from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_lorcana_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='back_image',
            field=models.ImageField(blank=True, help_text='The back side of the card', null=True, upload_to='cards/backs/'),
        ),
    ]
