from django.db.models import Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api.models import (
    User, Product, Inventory, Order, OrderItem, 
    CompetitorPrice, Notification, ConversationHistory
)

def find_product_listings(user, product_name: str, requested_quantity: float) -> list:
    """
    Finds all suppliers who have enough stock of a product.
    Returns a price-sorted list of supplier options.
    """
    try:
        # Find the product by name (case-insensitive search)
        product = Product.objects.filter(
            Q(product_name__icontains=product_name) | 
            Q(internal_name__icontains=product_name)
        ).first()
        
        if not product:
            return []
        
        # Find inventory items with sufficient quantity
        inventory_items = Inventory.objects.filter(
            product=product,
            quantity_available__gte=requested_quantity,
            status='active'
        ).select_related('supplier').order_by('price_per_unit_etb')
        
        # Format results
        results = []
        for item in inventory_items:
            results.append({
                'supplier_name': item.supplier.username,
                'supplier_id': str(item.supplier.id),
                'quantity_available': float(item.quantity_available),
                'price_per_unit': float(item.price_per_unit_etb),
                'total_price': float(item.price_per_unit_etb) * requested_quantity,
                'available_date': item.available_date.isoformat(),
                'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
                'image_url': item.image_url if item.image_url else None,
            })
        
        return results
        
    except Exception as e:
        print(f"Error in find_product_listings: {e}")
        return []


def create_order_in_db(user, items: list, delivery_date: str, delivery_location: str) -> dict:
    """
    Creates a new order with multiple items.
    items format: [{'product_name': str, 'quantity': float, 'supplier_id': str}, ...]
    Returns order details or error.
    """
    try:
        # Validate user is a customer
        if user.role != 'customer':
            return {'error': 'Only customers can create orders'}
        
        # Create the order
        order = Order.objects.create(
            user=user,
            order_date=timezone.now(),
            status='pending_acceptance'
        )
        
        suppliers_involved = {}  # Changed to dict to track items per supplier
        order_items_created = []
        
        # Create order items
        for item_data in items:
            # Find product
            product = Product.objects.filter(
                Q(product_name__icontains=item_data['product_name']) |
                Q(internal_name__icontains=item_data['product_name'])
            ).first()
            
            if not product:
                continue
            
            # Find inventory item
            inventory = Inventory.objects.filter(
                product=product,
                supplier_id=item_data['supplier_id'],
                status='active'
            ).first()
            
            if not inventory:
                continue
            
            # Create order item with supplier reference
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                supplier=inventory.supplier,
                quantity=item_data['quantity'],
                price_per_unit_etb=inventory.price_per_unit_etb
            )
            
            item_details = {
                'product': product.product_name,
                'quantity': float(item_data['quantity']),
                'price_per_unit': float(inventory.price_per_unit_etb),
                'subtotal': float(inventory.price_per_unit_etb * item_data['quantity'])
            }
            
            order_items_created.append(item_details)
            
            # Track items per supplier
            if inventory.supplier not in suppliers_involved:
                suppliers_involved[inventory.supplier] = []
            suppliers_involved[inventory.supplier].append(item_details)
        
        # Send order notifications to suppliers as chat messages
        for supplier, supplier_items in suppliers_involved.items():
            
            # Create detailed order notification message
            notification_message = f"""🛒 **NEW ORDER RECEIVED**

**Order ID:** #{order.order_id}
**Customer:** {user.username}
**Order Date:** {order.order_date.strftime('%Y-%m-%d %H:%M')}
**Delivery Date:** {delivery_date}
**Delivery Location:** {delivery_location}

**Items Ordered:**
"""
            
            total_amount = 0
            for item in supplier_items:
                notification_message += f"• {item['product']}: {item['quantity']} units @ {item['price_per_unit']} ETB = {item['subtotal']} ETB\n"
                total_amount += item['subtotal']
            
            notification_message += f"""
**Total Amount:** {total_amount} ETB
**Status:** Pending Your Response

Please review the order details and respond by accepting or declining this order."""
            
            # Save as chat message in supplier's conversation history
            chat_message = ConversationHistory.objects.create(
                user=supplier,
                sender='bot',
                message=notification_message,
                message_type='order_notification',
                order=order
            )
            
            # Send via WebSocket to supplier's chat
            try:
                channel_layer = get_channel_layer()
                user_group_name = f'user_{supplier.id}'
                async_to_sync(channel_layer.group_send)(
                    user_group_name,
                    {
                        'type': 'chat_message',
                        'message': notification_message,
                        'message_type': 'order_notification',
                        'order_id': str(order.order_id),
                        'timestamp': chat_message.timestamp.isoformat()
                    }
                )
            except Exception as e:
                print(f"Error sending chat notification to supplier: {e}")
        
        return {
            'success': True,
            'order_id': str(order.order_id),
            'order_date': order.order_date.isoformat(),
            'status': order.status,
            'delivery_date': delivery_date,
            'delivery_location': delivery_location,
            'items': order_items_created,
            'total': sum(item['subtotal'] for item in order_items_created)
        }
        
    except Exception as e:
        print(f"Error in create_order_in_db: {e}")
        return {'error': str(e)}


def check_existing_inventory(user, product_name: str) -> dict:
    """
    Checks if the authenticated supplier has inventory for a product.
    Returns inventory details or None.
    """
    try:
        # Validate user is a supplier
        if user.role != 'supplier':
            return None
        
        # Find product
        product = Product.objects.filter(
            Q(product_name__icontains=product_name) |
            Q(internal_name__icontains=product_name)
        ).first()
        
        if not product:
            return None
        
        # Find inventory
        inventory = Inventory.objects.filter(
            supplier=user,
            product=product
        ).first()
        
        if not inventory:
            return None
        
        return {
            'inventory_id': str(inventory.inventory_id),
            'product_name': product.product_name,
            'quantity_available': float(inventory.quantity_available),
            'price_per_unit': float(inventory.price_per_unit_etb),
            'status': inventory.status,
            'available_date': inventory.available_date.isoformat(),
            'expiry_date': inventory.expiry_date.isoformat() if inventory.expiry_date else None
        }
        
    except Exception as e:
        print(f"Error in check_existing_inventory: {e}")
        return None


def get_comprehensive_pricing_suggestion(user, product_name: str, days_of_history: int = 30) -> dict:
    """
    Provides pricing suggestions based on competitor prices and historical sales.
    Returns market insights.
    """
    try:
        # Find product
        product = Product.objects.filter(
            Q(product_name__icontains=product_name) |
            Q(internal_name__icontains=product_name)
        ).first()
        
        if not product:
            return {'error': 'Product not found'}
        
        # Calculate date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_of_history)
        
        # Query competitor prices
        competitor_prices = CompetitorPrice.objects.filter(
            product=product,
            date__gte=start_date,
            date__lte=end_date
        ).values('competitor_tier').annotate(avg_price=Avg('price_per_unit_etb'))
        
        competitor_avg = {}
        for cp in competitor_prices:
            competitor_avg[cp['competitor_tier']] = float(cp['avg_price'])
        
        # Query highest-volume sales price in last 30 days
        recent_orders = OrderItem.objects.filter(
            product=product,
            order__order_date__gte=timezone.now() - timedelta(days=30)
        ).order_by('-quantity').first()
        
        highest_volume_price = None
        if recent_orders:
            highest_volume_price = float(recent_orders.price_per_unit_etb)
        
        return {
            'product_name': product.product_name,
            'competitor_averages': competitor_avg,
            'highest_volume_price_last_30_days': highest_volume_price,
            'analysis_period_days': days_of_history,
            'recommendation': _generate_price_recommendation(competitor_avg, highest_volume_price)
        }
        
    except Exception as e:
        print(f"Error in get_comprehensive_pricing_suggestion: {e}")
        return {'error': str(e)}


def _generate_price_recommendation(competitor_avg: dict, volume_price: float) -> str:
    """Helper function to generate pricing recommendation text."""
    if not competitor_avg and not volume_price:
        return "Insufficient market data for recommendation."
    
    prices = list(competitor_avg.values())
    if volume_price:
        prices.append(volume_price)
    
    if prices:
        avg_market = sum(prices) / len(prices)
        return f"Suggested price range: {avg_market * 0.9:.2f} - {avg_market * 1.1:.2f} ETB per unit"
    
    return "Unable to generate recommendation."


def add_or_update_inventory(user, details: dict) -> dict:
    """
    Adds new inventory or updates existing inventory for a supplier.
    details: {'product_name': str, 'quantity': float, 'price': float, 
              'available_date': str, 'expiry_date': str (optional)}
    """
    try:
        # Validate user is a supplier
        if user.role != 'supplier':
            return {'error': 'Only suppliers can manage inventory'}
        
        # Find or create product
        product = Product.objects.filter(
            Q(product_name__icontains=details['product_name']) |
            Q(internal_name__icontains=details['product_name'])
        ).first()
        
        if not product:
            return {'error': f"Product '{details['product_name']}' not found"}
        
        # Parse dates
        available_date = datetime.fromisoformat(details['available_date']).date() if isinstance(details['available_date'], str) else details['available_date']
        expiry_date = None
        if details.get('expiry_date'):
            expiry_date = datetime.fromisoformat(details['expiry_date']).date() if isinstance(details['expiry_date'], str) else details['expiry_date']
        
        # Update or create inventory
        defaults_dict = {
            'quantity_available': details['quantity'],
            'price_per_unit_etb': details['price'],
            'available_date': available_date,
            'expiry_date': expiry_date,
            'status': 'active'
        }
        
        # Add image_url if provided
        if details.get('image_url'):
            defaults_dict['image_url'] = details['image_url']
        
        inventory, created = Inventory.objects.update_or_create(
            supplier=user,
            product=product,
            defaults=defaults_dict
        )
        
        action = 'created' if created else 'updated'
        
        return {
            'success': True,
            'action': action,
            'inventory_id': str(inventory.inventory_id),
            'product_name': product.product_name,
            'quantity': float(inventory.quantity_available),
            'price_per_unit': float(inventory.price_per_unit_etb)
        }
        
    except Exception as e:
        print(f"Error in add_or_update_inventory: {e}")
        return {'error': str(e)}


def get_supplier_inventory(user) -> dict:
    """
    Fetches all active inventory listings for the authenticated supplier.
    Also checks for items expiring within 5 days and alerts the supplier.
    """
    try:
        # Validate user is a supplier
        if user.role != 'supplier':
            return {'inventory': [], 'expiring_soon': []}
        
        from datetime import date
        today = date.today()
        five_days_from_now = today + timedelta(days=5)
        
        inventory_items = Inventory.objects.filter(
            supplier=user,
            status='active'
        ).select_related('product').order_by('-available_date')
        
        all_inventory = []
        expiring_soon = []
        
        for item in inventory_items:
            item_data = {
                'inventory_id': str(item.inventory_id),
                'product_name': item.product.product_name,
                'quantity_available': float(item.quantity_available),
                'price_per_unit': float(item.price_per_unit_etb),
                'available_date': item.available_date.isoformat(),
                'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None
            }
            
            all_inventory.append(item_data)
            
            # Check if expiring within 5 days
            if item.expiry_date and item.expiry_date <= five_days_from_now:
                days_until_expiry = (item.expiry_date - today).days
                expiring_soon.append({
                    **item_data,
                    'days_until_expiry': days_until_expiry,
                    'expires_on': item.expiry_date.strftime('%Y-%m-%d')
                })
        
        return {
            'inventory': all_inventory,
            'expiring_soon': expiring_soon,
            'has_expiring_items': len(expiring_soon) > 0
        }
        
    except Exception as e:
        print(f"Error in get_supplier_inventory: {e}")
        return {'inventory': [], 'expiring_soon': [], 'has_expiring_items': False}


def get_supplier_orders(user, status_filter: str = None, date_filter: str = None) -> dict:
    """
    Fetches all orders that contain items from this supplier.
    Returns orders grouped by status.
    
    Args:
        user: The supplier user
        status_filter: Optional filter by status ('accepted', 'pending_acceptance', 'declined', 'completed', 'out_for_delivery')
        date_filter: Optional filter by date ('today', 'yesterday', or specific date in YYYY-MM-DD format)
    """
    try:
        # Validate user is a supplier
        if user.role != 'supplier':
            return {'error': 'Only suppliers can view orders'}
        
        from datetime import date, timedelta
        
        # Find all order items from this supplier
        order_items_query = OrderItem.objects.filter(
            supplier=user
        ).select_related('order', 'product', 'order__user')
        
        # Apply date filter if provided
        if date_filter:
            today = date.today()
            if date_filter == 'today':
                order_items_query = order_items_query.filter(order__order_date__date=today)
            elif date_filter == 'yesterday':
                yesterday = today - timedelta(days=1)
                order_items_query = order_items_query.filter(order__order_date__date=yesterday)
            else:
                # Try parsing as specific date
                try:
                    from datetime import datetime
                    specific_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    order_items_query = order_items_query.filter(order__order_date__date=specific_date)
                except ValueError:
                    pass
        
        # Apply status filter if provided
        if status_filter:
            order_items_query = order_items_query.filter(order__status=status_filter)
        
        order_items = order_items_query
        
        # Group orders by status
        orders_by_status = {
            'pending_acceptance': [],
            'accepted': [],
            'declined': [],
            'out_for_delivery': [],
            'completed': []
        }
        
        seen_orders = set()
        
        for order_item in order_items:
            order = order_item.order
            
            # Skip if we've already processed this order
            if order.order_id in seen_orders:
                continue
            seen_orders.add(order.order_id)
            
            # Get all items for this order from this supplier
            supplier_items = OrderItem.objects.filter(
                order=order,
                supplier=user
            ).select_related('product')
            
            items_list = []
            total_amount = 0
            for item in supplier_items:
                quantity = float(item.quantity)
                price = float(item.price_per_unit_etb)
                item_total = quantity * price
                items_list.append({
                    'product': item.product.product_name,
                    'quantity': quantity,
                    'price_per_unit': price,
                    'subtotal': item_total
                })
                total_amount += item_total
            
            order_data = {
                'order_id': str(order.order_id),
                'customer': order.user.username if order.user else 'Unknown',
                'order_date': order.order_date.strftime('%Y-%m-%d %H:%M'),
                'status': order.status,
                'items': items_list,
                'total_amount': total_amount
            }
            
            if order.status in orders_by_status:
                orders_by_status[order.status].append(order_data)
        
        # Count orders by status
        order_counts = {status: len(orders) for status, orders in orders_by_status.items()}
        
        return {
            'orders': orders_by_status,
            'counts': order_counts,
            'total_orders': sum(order_counts.values())
        }
        
    except Exception as e:
        print(f"Error in get_supplier_orders: {e}")
        return {'error': str(e)}


def update_order_status(user, order_id: str, new_status: str, decline_reason: str = '') -> dict:
    """
    Allows a supplier to accept or decline an order.
    Verifies the order contains items from this supplier.
    """
    try:
        # Validate user is a supplier
        if user.role != 'supplier':
            return {'error': 'Only suppliers can update order status'}
        
        # Find the order
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return {'error': 'Order not found'}
        
        # Verify this supplier has items in this order
        supplier_items = OrderItem.objects.filter(
            order=order,
            supplier=user
        ).exists()
        
        if not supplier_items:
            return {'error': 'You do not have items in this order'}
        
        # Validate status
        valid_statuses = ['accepted', 'declined']
        if new_status not in valid_statuses:
            return {'error': f'Invalid status. Must be one of: {valid_statuses}'}
        
        # Update order status
        order.status = new_status
        order.save()
        
        # Send chat message to customer
        if order.user:
            status_text = 'accepted ✅' if new_status == 'accepted' else 'declined ❌'
            status_emoji = '✅' if new_status == 'accepted' else '❌'
            
            customer_message = f"""{status_emoji} **ORDER {new_status.upper()}**

Your order **#{order.order_id}** has been **{status_text}** by {user.username}."""
            
            if new_status == 'declined' and decline_reason:
                customer_message += f"\n\n**Reason:** {decline_reason}"
            elif new_status == 'accepted':
                customer_message += "\n\nYou will receive updates about your order delivery soon."
            
            # Save as chat message in customer's conversation history
            chat_message = ConversationHistory.objects.create(
                user=order.user,
                sender='bot',
                message=customer_message,
                message_type='order_response',
                order=order
            )
            
            # Send via WebSocket to customer's chat
            try:
                channel_layer = get_channel_layer()
                user_group_name = f'user_{order.user.id}'
                async_to_sync(channel_layer.group_send)(
                    user_group_name,
                    {
                        'type': 'chat_message',
                        'message': customer_message,
                        'message_type': 'order_response',
                        'order_id': str(order.order_id),
                        'timestamp': chat_message.timestamp.isoformat()
                    }
                )
            except Exception as e:
                print(f"Error sending chat message to customer: {e}")
        
        return {
            'success': True,
            'order_id': str(order.order_id),
            'new_status': new_status,
            'message': f'Order {new_status} successfully'
        }
        
    except Exception as e:
        print(f"Error in update_order_status: {e}")
        return {'error': str(e)}

