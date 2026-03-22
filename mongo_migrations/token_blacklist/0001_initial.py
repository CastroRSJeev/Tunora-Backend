from django.db import migrations, models
import django_mongodb_backend.fields


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OutstandingToken',
            fields=[
                ('id', django_mongodb_backend.fields.ObjectIdAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jti', models.CharField(max_length=255, unique=True)),
                ('token', models.TextField()),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=models.SET_NULL,
                    to='users.user',
                )),
            ],
            options={
                'ordering': ('user',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BlacklistedToken',
            fields=[
                ('id', django_mongodb_backend.fields.ObjectIdAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blacklisted_at', models.DateTimeField(auto_now_add=True)),
                ('token', models.OneToOneField(
                    on_delete=models.CASCADE,
                    to='token_blacklist.outstandingtoken',
                )),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
