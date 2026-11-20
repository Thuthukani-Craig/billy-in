from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="issued_snapshot",
            field=models.JSONField(blank=True, default=dict, editable=False),
        ),
        migrations.AddField(
            model_name="document",
            name="issued_snapshot_at",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
