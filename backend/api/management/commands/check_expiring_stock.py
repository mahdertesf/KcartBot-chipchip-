from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import Inventory, Notification


class Command(BaseCommand):
    help = 'Checks for expiring inventory and creates notifications for suppliers'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days before expiry to trigger notification (default: 7)'
        )
    
    def handle(self, *args, **options):
        days_threshold = options['days']
        
        # Calculate the threshold date
        threshold_date = timezone.now().date() + timedelta(days=days_threshold)
        
        # Find inventory items expiring soon
        expiring_items = Inventory.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=threshold_date,
            expiry_date__gte=timezone.now().date(),
            status='active'
        ).select_related('supplier', 'product')
        
        notifications_created = 0
        
        for item in expiring_items:
            days_until_expiry = (item.expiry_date - timezone.now().date()).days
            
            # Check if notification already exists for this specific inventory item
            # We check for notifications created in the last 24 hours for the same inventory
            recent_notification = Notification.objects.filter(
                user=item.supplier,
                inventory=item,
                notification_type='expiry_alert',
                created_at__gte=timezone.now() - timedelta(days=1)
            ).exists()
            
            if not recent_notification:
                # Create notification
                message = (
                    f"Stock Expiry Alert: Your {item.product.product_name} "
                    f"inventory ({item.quantity_available} {item.product.unit}) "
                    f"will expire in {days_until_expiry} day(s) on {item.expiry_date.strftime('%Y-%m-%d')}. "
                    f"Consider reducing prices or promoting this product."
                )
                
                Notification.objects.create(
                    user=item.supplier,
                    message=message,
                    inventory=item,
                    notification_type='expiry_alert'
                )
                
                notifications_created += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created notification for {item.supplier.username} - {item.product.product_name}"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Check complete. Created {notifications_created} notification(s)."
            )
        )

