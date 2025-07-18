from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientservice',
            name='admin_status',
            field=models.CharField(
                choices=[('ENABLED', 'Habilitado'), ('DISABLED', 'Deshabilitado administrativamente')],
                default='ENABLED',
                help_text='Control administrativo independiente del estado operacional',
                max_length=15,
                verbose_name='Estado administrativo'
            ),
        ),
    ]
