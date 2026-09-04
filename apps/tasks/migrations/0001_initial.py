import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lists', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=512)),
                ('notes', models.TextField(blank=True)),
                ('done', models.BooleanField(default=False)),
                ('important', models.BooleanField(default=False)),
                ('my_day', models.BooleanField(default=False)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('reminder_at', models.DateTimeField(blank=True, null=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('done_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to=settings.AUTH_USER_MODEL)),
                ('task_list', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='lists.tasklist')),
            ],
            options={
                'db_table': 'tasks_task',
                'ordering': ['sort_order', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='Step',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=512)),
                ('done', models.BooleanField(default=False)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='tasks.task')),
            ],
            options={
                'db_table': 'tasks_step',
                'ordering': ['sort_order', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['user', 'done', 'is_deleted'], name='tasks_task_user_id_done_is_deleted_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['user', 'my_day'], name='tasks_task_user_id_my_day_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['user', 'important'], name='tasks_task_user_id_important_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['user', 'due_date'], name='tasks_task_user_id_due_date_idx'),
        ),
    ]
