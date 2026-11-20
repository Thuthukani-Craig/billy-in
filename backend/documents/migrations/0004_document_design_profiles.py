import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("businesses", "0001_initial"),
        ("documents", "0003_issued_document_snapshot"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentDesignProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("document_type", models.CharField(choices=[("QUOTATION", "Quotation"), ("INVOICE", "Invoice"), ("RECEIPT", "Receipt")], max_length=20)),
                ("theme", models.CharField(choices=[("CLASSIC", "Classic"), ("MODERN", "Modern"), ("MINIMAL", "Minimal"), ("CORPORATE", "Corporate"), ("BOLD", "Bold"), ("INDUSTRIAL", "Industrial")], default="CLASSIC", max_length=20)),
                ("primary_colour", models.CharField(blank=True, max_length=7)),
                ("show_logo", models.BooleanField(default=True)),
                ("show_payment_details", models.BooleanField(default=True)),
                ("show_business_registration", models.BooleanField(default=True)),
                ("show_customer_vat_number", models.BooleanField(default=True)),
                ("design_tokens", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="document_design_profiles", to="businesses.business")),
            ],
        ),
        migrations.AddConstraint(
            model_name="documentdesignprofile",
            constraint=models.UniqueConstraint(fields=("business", "document_type"), name="unique_business_document_design"),
        ),
    ]
