from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='franchise',
            field=models.CharField(choices=[('OP', 'One Piece'), ('DI', 'Lorcana')], max_length=2),
        ),
    ]
