from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoicing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='reference',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
