from django.db import migrations, models


def move_testgroup_table(apps, schema_editor):
    db = schema_editor.connection
    existing_tables = db.introspection.table_names()
    if "testgroups_testgroup" in existing_tables:
        schema_editor.execute(
            "ALTER TABLE testgroups_testgroup RENAME TO networktests_testgroup"
        )
        if "testgroups_testgroup_testcases" in existing_tables:
            schema_editor.execute(
                "ALTER TABLE testgroups_testgroup_testcases RENAME TO networktests_testgroup_testcases"
            )
        elif "networktests_testgroup_testcases" not in existing_tables:
            TestGroup = apps.get_model("networktests", "TestGroup")
            through = TestGroup._meta.get_field("testcases").remote_field.through
            schema_editor.create_model(through)
    elif "networktests_testgroup" not in existing_tables:
        TestGroup = apps.get_model("networktests", "TestGroup")
        schema_editor.create_model(TestGroup)


def reverse_move_testgroup_table(apps, schema_editor):
    db = schema_editor.connection
    existing_tables = db.introspection.table_names()
    if "networktests_testgroup" in existing_tables:
        schema_editor.execute(
            "ALTER TABLE networktests_testgroup RENAME TO testgroups_testgroup"
        )
    if "networktests_testgroup_testcases" in existing_tables:
        schema_editor.execute(
            "ALTER TABLE networktests_testgroup_testcases RENAME TO testgroups_testgroup_testcases"
        )


def migrate_contenttype(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    try:
        ct = ContentType.objects.get(app_label="testgroups", model="testgroup")
        ct.app_label = "networktests"
        ct.save()
    except ContentType.DoesNotExist:
        pass


def reverse_migrate_contenttype(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    try:
        ct = ContentType.objects.get(
            app_label="networktests", model="testgroup"
        )
        ct.app_label = "testgroups"
        ct.save()
    except ContentType.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("networktests", "0007_customtesttemplate_updated_at_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="TestGroup",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("name", models.CharField(max_length=50, unique=True)),
                        (
                            "testcases",
                            models.ManyToManyField(to="networktests.testcase"),
                        ),
                    ],
                ),
            ],
        ),
        migrations.RunPython(
            move_testgroup_table, reverse_move_testgroup_table
        ),
        migrations.RunPython(migrate_contenttype, reverse_migrate_contenttype),
    ]
