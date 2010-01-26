# Project permissions required
# FIXME: It could be a dictionary with better key naming instead of a bunch of 
# variables
pr_project_add = (
    ('general',  'projects.add_project'),
)

pr_project_add_change = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.change_project'),
)

pr_project_delete = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.delete_project'),
)

pr_project_view_log = (
    ('granular', 'project_perm.maintain'),
)


pr_project_add_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.add_permission'),
)

pr_project_approve_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.approve_permission_requests'),
)

pr_project_delete_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.delete_permission'),
)

# Component permissions required
pr_component_add_change = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.add_component'),
    ('general',  'projects.change_component'),
)

pr_component_delete = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.delete_component'),
)

pr_component_set_stats = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.refresh_stats'),
)

pr_component_clear_cache = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.clear_cache'),
)

pr_component_submit_file = (
    ('granular', 'project_perm.maintain'),
    ('granular', 'project_perm.submit_file'),
    ('general',  'projects.submit_file'),
)

pr_component_lock_file = (
    ('granular', 'project_perm.maintain'),
    ('granular', 'project_perm.submit_file'),
    ('general',  'translations.add_pofilelock'),
    ('general',  'translations.delete_pofilelock'),
)

pr_component_watch_file = (
    ('granular', 'project_perm.submit_file'),
    ('general',  'repowatch.add_watch'),
    ('general',  'repowatch.delete_watch'),
)


# Release permissions required

pr_release_add_change = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.add_release'),
    ('general',  'projects.change_release'),
)

pr_release_delete = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.delete_release'),
)
