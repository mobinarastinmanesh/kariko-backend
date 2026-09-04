import os

# Force test settings before pytest-django initialises Django.
# The container env var DJANGO_SETTINGS_MODULE=config.settings.development
# would otherwise override pytest.ini, pulling in debug_toolbar (not installed).
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
