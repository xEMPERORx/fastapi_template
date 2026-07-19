"""Redis keys/channel shared between the publisher (repositories, on
mutation) and the subscriber (`AuthzCache`, one per worker process)."""

AUTHZ_EVENTS_CHANNEL = "authz:events"
PERM_VERSIONS_KEY = "authz:perm_versions"
INACTIVE_USERS_KEY = "authz:inactive_users"
INACTIVE_TENANTS_KEY = "authz:inactive_tenants"
RESYNC_INTERVAL_SECONDS = 15
