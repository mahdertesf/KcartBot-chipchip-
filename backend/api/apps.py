from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """
        Import signals and start scheduler when the app is ready.
        """
        import api.signals
        
        # Start the scheduler (only in production/development server, not in migrations)
        import sys
        if 'runserver' in sys.argv or 'daphne' in sys.argv:
            from api.scheduler import start_scheduler
            start_scheduler()