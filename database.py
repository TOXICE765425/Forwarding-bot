from firebase import (
    ensure_user, get_user, update_user, get_sources, add_source, remove_source,
    set_position, get_pending_deletions, add_cleanup, remove_cleanup, stats
)

# Compatibility wrapper: keeps storage limited to metadata/counters.
