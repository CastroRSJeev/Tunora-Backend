from django.db import migrations, models
import django.utils.timezone
import django_mongodb_backend.fields


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('contenttypes', '0001_initial'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', django_mongodb_backend.fields.ObjectIdAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_time', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='action time')),
                ('object_id', models.TextField(blank=True, null=True, verbose_name='object id')),
                ('object_repr', models.CharField(max_length=200, verbose_name='object repr')),
                ('action_flag', models.PositiveSmallIntegerField(verbose_name='action flag')),
                ('change_message', models.TextField(blank=True, verbose_name='change message')),
                ('content_type', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.SET_NULL,
                    to='contenttypes.contenttype',
                    verbose_name='content type',
                )),
                ('user', models.ForeignKey(
                    on_delete=models.CASCADE,
                    to='users.user',
                    verbose_name='user',
                )),
            ],
            options={
                'verbose_name': 'log entry',
                'verbose_name_plural': 'log entries',
                'db_table': 'django_admin_log',
                'ordering': ['-action_time'],
            },
        ),
    ]
