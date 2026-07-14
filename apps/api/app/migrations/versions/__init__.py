"""Migration versions — ordered list of all formal migrations.

Add new migrations at the end. Never reorder or remove applied versions.
"""

from app.migrations.base import Migration
from app.migrations.versions.backfill_participant_country_codes import (
    BackfillParticipantCountryCodesMigration,
)
from app.migrations.versions.backfill_schedule_is_active import (
    BackfillScheduleIsActiveMigration,
)
from app.migrations.versions.backfill_sync_metadata import (
    BackfillSyncMetadataMigration,
)
from app.migrations.versions.configure_lajuana_settings import (
    ConfigureLaJuanaSettingsMigration,
)
from app.migrations.versions.migrate_provider_fields import (
    MigrateProviderFieldsMigration,
)
from app.migrations.versions.staff_to_guide import StaffToGuideMigration

# Order matters — run in sequence, oldest first.
# Never remove entries from this list once deployed.
MIGRATIONS: list[Migration] = [
    StaffToGuideMigration(),
    BackfillScheduleIsActiveMigration(),
    BackfillSyncMetadataMigration(),
    MigrateProviderFieldsMigration(),
    ConfigureLaJuanaSettingsMigration(),
    BackfillParticipantCountryCodesMigration(),
]
