from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from api.models import ConversationHistory, Notification
from api.utils.translator import identify_language, translate_to_english, translate_from_english
from api.agent.factory import create_kcart_agent


class ChatAPIView(APIView):
    """
    Handles chat messages from users (authenticated or not).
    Supports multi-language input/output via translation layer.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Extract message from request
            user_message = request.data.get('message', '').strip()
            if not user_message:
                return Response(
                    {'error': 'Message is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get conversation history if provided
            chat_history = request.data.get('history', [])
            
            # ============ LANGUAGE IDENTIFICATION ============
            detected_language = identify_language(user_message)
            
            # Store language in session for consistency
            request.session['user_language'] = detected_language
            
            # Handle unsupported languages
            if detected_language == 'other':
                return Response({
                    'reply': 'Sorry, I currently only support English and Amharic. Please use one of these languages.',
                    'language': 'english'
                })
            
            # ============ TRANSLATION TO ENGLISH ============
            english_message = user_message
            if detected_language in ['amharic', 'amharic_latin']:
                english_message = translate_to_english(user_message)
            
            # ============ AGENT EXECUTION ============
            # Create agent based on user authentication
            user = request.user if request.user.is_authenticated else None
            agent = create_kcart_agent(user)
            
            # Format chat history for agent
            history_text = ""
            if chat_history:
                for msg in chat_history[-10:]:  # Last 10 messages for context
                    sender = msg.get('sender', 'user')
                    content = msg.get('message', '')
                    history_text += f"{sender}: {content}\n"
            
            # Convert chat history to LangChain message format
            from langchain_core.messages import HumanMessage, AIMessage
            chat_history_messages = []
            if chat_history:
                for msg in chat_history[-10:]:  # Last 10 messages
                    sender = msg.get('sender', 'user')
                    content = msg.get('message', '')
                    if sender == 'user':
                        chat_history_messages.append(HumanMessage(content=content))
                    elif sender == 'bot':
                        chat_history_messages.append(AIMessage(content=content))
            
            # Run agent with context
            try:
                agent_response = agent.invoke({
                    'input': english_message,
                    'chat_history': chat_history_messages
                })
                
                # Extract the output
                agent_reply_english = agent_response.get('output', 'I apologize, but I encountered an error processing your request.')
                
            except Exception as agent_error:
                print(f"Agent execution error: {agent_error}")
                agent_reply_english = "I apologize, but I'm having trouble processing your request right now. Please try again."
            
            # ============ TRANSLATION BACK TO USER'S LANGUAGE ============
            final_reply = agent_reply_english
            if detected_language in ['amharic', 'amharic_latin']:
                final_reply = translate_from_english(agent_reply_english, detected_language)
            
            # Safety check for empty responses
            if not final_reply or not final_reply.strip():
                final_reply = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
            
            # ============ SAVE CONVERSATION HISTORY ============
            if request.user.is_authenticated:
                # Save user message
                ConversationHistory.objects.create(
                    user=request.user,
                    sender='user',
                    message=user_message
                )
                
                # Save bot reply
                ConversationHistory.objects.create(
                    user=request.user,
                    sender='bot',
                    message=final_reply
                )
            
            # ============ RETURN RESPONSE ============
            return Response({
                'reply': final_reply,
                'language': detected_language,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error in ChatAPIView: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        """
        Retrieves conversation history for authenticated users.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Get user's conversation history
            history = ConversationHistory.objects.filter(
                user=request.user
            ).order_by('timestamp')[:100]  # Last 100 messages
            
            from api.serializers import ConversationHistorySerializer
            history_data = ConversationHistorySerializer(history, many=True).data
            
            return Response({
                'history': history_data
            })
            
        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return Response(
                {'error': 'Failed to retrieve chat history'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationAPIView(APIView):
    """
    Handles notifications for authenticated users.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Fetches all unsent notifications for the authenticated user.
        Marks them as sent after retrieval.
        """
        try:
            # Get unsent notifications
            notifications = Notification.objects.filter(
                user=request.user,
                is_sent=False
            ).order_by('created_at')
            
            # Prepare notification data
            notification_data = []
            notification_ids = []
            
            for notif in notifications:
                notification_data.append({
                    'id': notif.id,
                    'message': notif.message,
                    'created_at': notif.created_at.isoformat()
                })
                notification_ids.append(notif.id)
            
            # Mark notifications as sent
            if notification_ids:
                Notification.objects.filter(
                    id__in=notification_ids
                ).update(is_sent=True)
            
            return Response({
                'notifications': notification_data,
                'count': len(notification_data)
            })
            
        except Exception as e:
            print(f"Error in NotificationAPIView: {e}")
            return Response(
                {'error': 'Failed to retrieve notifications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderActionAPIView(APIView):
    """
    Handles order acceptance/decline actions by suppliers.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Accept or decline an order.
        Expected data: {'order_id': str, 'action': 'accept'|'decline', 'reason': str (optional)}
        """
        try:
            order_id = request.data.get('order_id')
            action = request.data.get('action')  # 'accept' or 'decline'
            reason = request.data.get('reason', '')
            
            if not order_id or not action:
                return Response(
                    {'error': 'order_id and action are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if action not in ['accept', 'decline']:
                return Response(
                    {'error': 'action must be either "accept" or "decline"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert action to status
            new_status = 'accepted' if action == 'accept' else 'declined'
            
            # Use database_tool to update order status
            # This will handle sending chat messages to customer via WebSocket
            from api.tools import database_tool
            result = database_tool.update_order_status(request.user, order_id, new_status, decline_reason=reason)
            
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'success': True,
                'message': f'Order {action}ed successfully',
                'order_status': new_status
            })
            
        except Exception as e:
            print(f"Error in OrderActionAPIView: {e}")
            return Response(
                {'error': 'Failed to process order action'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
