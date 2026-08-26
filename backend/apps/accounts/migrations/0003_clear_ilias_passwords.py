from django.db import migrations, models


def clear_ilias_passwords(apps, schema_editor):
    IliasCredential = apps.get_model("accounts", "IliasCredential")
    IliasCredential.objects.exclude(ilias_password="").update(ilias_password="")


def noop_reverse(apps, schema_editor):
    # Intentionally irreversible: plaintext university passwords must not return.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_iliascredential_phpsessid_and_more"),
    ]

    operations = [
        migrations.RunPython(clear_ilias_passwords, noop_reverse),
        migrations.AlterField(
            model_name="iliascredential",
            name="ilias_password",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "Deprecated. University passwords are never persisted; "
                    "auth uses interactive browser MFA and session cookies only."
                ),
            ),
        ),
    ]
