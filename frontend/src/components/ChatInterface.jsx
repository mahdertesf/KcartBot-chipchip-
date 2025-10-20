import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { chatAPI, notificationAPI } from '../utils/api';
import wsClient from '../utils/websocket';
import ReactMarkdown from 'react-markdown';
import OrderNotification from './OrderNotification';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [followUpLoading, setFollowUpLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const { isAuthenticated, user, logout } = useAuth();

  useEffect(() => {
    // Load conversation history for authenticated users
    if (isAuthenticated) {
      loadHistory();
      // Fetch and mark notifications as sent
      fetchNotifications();
    } else {
      // Load from localStorage for unauthenticated users
      const savedMessages = localStorage.getItem('chatHistory');
      if (savedMessages) {
        try {
          const parsed = JSON.parse(savedMessages);
          setMessages(parsed.slice(-20)); // Last 20 messages
        } catch (error) {
          console.error('Error loading chat history:', error);
        }
      }
    }

    // Setup WebSocket listener for chat messages and notifications
    const handleWebSocketMessage = (data) => {
      if (data.type === 'chat_message') {
        // Add chat message (including order notifications)
        const chatMessage = {
          sender: 'bot',
          message: data.message,
          timestamp: data.timestamp,
          message_type: data.message_type || 'text',
          order_id: data.order_id,
        };
        setMessages((prev) => [...prev, chatMessage]);
      } else if (data.type === 'notification') {
        // Add notification as a system message
        const notificationMessage = {
          sender: 'system',
          message: data.message,
          timestamp: data.timestamp,
        };
        setMessages((prev) => [...prev, notificationMessage]);
        
        // Mark notification as sent by fetching from API
        if (isAuthenticated) {
          fetchNotifications();
        }
      }
    };

    wsClient.addListener(handleWebSocketMessage);

    return () => {
      wsClient.removeListener(handleWebSocketMessage);
    };
  }, [isAuthenticated]);

  useEffect(() => {
    // Scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Save to localStorage for unauthenticated users
    if (!isAuthenticated && messages.length > 0) {
      localStorage.setItem('chatHistory', JSON.stringify(messages.slice(-20)));
    }
  }, [messages, isAuthenticated]);

  const loadHistory = async () => {
    try {
      const data = await chatAPI.getHistory();
      console.log('Loaded history from API:', data);
      if (data.history && data.history.length > 0) {
        console.log(`Setting ${data.history.length} messages from history`);
        setMessages(data.history);
      } else {
        console.log('No history data received');
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const data = await notificationAPI.getNotifications();
      if (data.notifications && data.notifications.length > 0) {
        // Add notifications as system messages
        const notificationMessages = data.notifications.map(notif => ({
          sender: 'system',
          message: notif.message,
          timestamp: notif.created_at,
        }));
        
        setMessages((prev) => [...prev, ...notificationMessages]);
        console.log(`Fetched and marked ${data.count} notifications as sent`);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      sender: 'user',
      message: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      // Prepare history for API
      const historyForAPI = messages.map((msg) => ({
        sender: msg.sender,
        message: msg.message,
      }));

      const response = await chatAPI.sendMessage(inputMessage, historyForAPI);

      // Check for follow_up (coordinated loading simulation)
      if (response.follow_up) {
        setFollowUpLoading(true);
        setTimeout(() => {
          const botMessage = {
            sender: 'bot',
            message: response.reply,
            timestamp: response.timestamp,
            language: response.language,
          };
          setMessages((prev) => [...prev, botMessage]);
          setFollowUpLoading(false);
        }, response.follow_up.duration || 2000);
      } else {
        const botMessage = {
          sender: 'bot',
          message: response.reply,
          timestamp: response.timestamp,
          language: response.language,
        };
        setMessages((prev) => [...prev, botMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        sender: 'bot',
        message: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getMessageStyle = (sender) => {
    if (sender === 'user') {
      return 'chat-end';
    } else if (sender === 'system') {
      return 'chat-start';
    }
    return 'chat-start';
  };

  const getMessageBubbleStyle = (sender) => {
    if (sender === 'user') {
      return 'chat-bubble-primary';
    } else if (sender === 'system') {
      return 'chat-bubble-warning';
    }
    return 'chat-bubble-secondary';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white text-gray-800 p-6 shadow-lg border-b-2 border-red-600">
        {/* ChipChip Logo - Centered */}
        <div className="flex justify-center mb-4">
          <img src="/chipchiplogo.png" alt="ChipChip Logo" className="h-16 w-auto" />
        </div>
        
        {/* KcartBot Title and User Info */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/kcartbot.png" alt="KcartBot Logo" className="h-10 w-auto" />
            <div>
              <h2 className="text-xl font-bold text-red-600">KcartBot</h2>
              <p className="text-xs text-gray-600">
                {isAuthenticated
                  ? `Welcome, ${user?.username || 'User'}!`
                  : 'Your AI Assistant'}
              </p>
            </div>
          </div>
          
          {/* Auth Button */}
          <div>
            {isAuthenticated ? (
              <div className="dropdown dropdown-end">
                <div
                  tabIndex={0}
                  role="button"
                  className="btn btn-sm btn-circle avatar placeholder bg-red-600 text-white hover:bg-red-700 border-0"
                >
                  <span className="text-sm font-bold">
                    {user?.username?.charAt(0).toUpperCase()}
                  </span>
                </div>
                <ul
                  tabIndex={0}
                  className="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52"
                >
                  <li className="menu-title">
                    <span>{user?.username}</span>
                  </li>
                  <li>
                    <a className="justify-between">
                      Role
                      <span className="badge badge-sm badge-error">
                        {user?.role || 'customer'}
                      </span>
                    </a>
                  </li>
                  <li>
                    <a onClick={logout}>Logout</a>
                  </li>
                </ul>
              </div>
            ) : (
              <button
                className="btn btn-sm bg-red-600 text-white hover:bg-red-700 border-red-600"
                onClick={() => {
                  // Trigger auth modal from parent
                  const event = new CustomEvent('openAuthModal');
                  window.dispatchEvent(event);
                }}
              >
                Login
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 bg-red-50">
        {messages.length === 0 && (
          <div className="text-center text-gray-700 mt-8">
            <div className="flex items-center justify-center gap-4 mb-4">
              <img src="/chipchiplogo.png" alt="ChipChip" className="h-20 w-auto" />
              <span className="text-4xl text-red-600">+</span>
              <img src="/kcartbot.png" alt="KcartBot" className="h-20 w-auto" />
            </div>
            <p className="text-lg font-bold text-red-600">👋 Welcome to KcartBot!</p>
            <p className="mt-2 text-gray-700">Your AI assistant for ChipChip marketplace</p>
            <p className="mt-1 text-sm text-gray-600">Ask me anything about products, orders, or Ethiopian agriculture</p>
          </div>
        )}
        
        {/* Debug: Show message count */}
        {messages.length > 0 && console.log(`Rendering ${messages.length} messages`)}

        {messages.map((msg, index) => (
          <div key={index} className={`chat ${getMessageStyle(msg.sender)}`}>
            <div className="chat-header">
              {msg.sender === 'user'
                ? 'You'
                : msg.sender === 'system'
                ? '🔔 Notification'
                : 'KcartBot'}
              <time className="text-xs opacity-50 ml-2">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </time>
            </div>
            <div className={`chat-bubble ${getMessageBubbleStyle(msg.sender)} ${msg.sender === 'user' ? 'bg-red-600 text-white' : ''}`}>
              {msg.sender === 'user' ? (
                msg.message
              ) : msg.message_type === 'order_notification' ? (
                <OrderNotification 
                  message={msg.message}
                  orderId={msg.order_id}
                  onActionComplete={(action, orderId) => {
                    console.log(`Order ${orderId} ${action}`);
                    // Remove the notification message after action
                    setMessages((prev) => prev.filter((m) => m.order_id !== orderId));
                  }}
                />
              ) : (
                <div className="markdown-content">
                  {(() => {
                    // Safety check for message content
                    if (!msg.message) {
                      return <span className="text-gray-400 italic">Empty message</span>;
                    }
                    
                    // Check if user is a supplier and message contains image URLs
                    const hasImageUrl = user?.role === 'supplier' && /https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp)/i.test(msg.message);
                    
                    if (hasImageUrl) {
                      // For suppliers: Show images by parsing and replacing URLs
                      const parts = msg.message.split(/(https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp))/gi);
                      
                      return (
                        <div>
                          {parts.map((part, index) => {
                            if (/^https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp)$/i.test(part)) {
                              return (
                                <div key={index} className="my-3">
                                  <img 
                                    src={part} 
                                    alt="Product" 
                                    className="max-w-full h-auto rounded-lg border border-gray-300"
                                    style={{ maxHeight: '400px' }}
                                  />
                                </div>
                              );
                            }
                            return (
                              <ReactMarkdown
                                key={index}
                                components={{
                                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                  ul: ({ children }) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
                                  ol: ({ children }) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
                                  li: ({ children }) => <li className="mb-1">{children}</li>,
                                  strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                                  em: ({ children }) => <em className="italic">{children}</em>,
                                  code: ({ node, inline, ...props }) =>
                                    inline ? (
                                      <code className="bg-gray-200 text-gray-800 px-1 py-0.5 rounded text-sm" {...props} />
                                    ) : (
                                      <code className="block bg-gray-200 text-gray-800 p-2 rounded text-sm my-2 overflow-x-auto" {...props} />
                                    ),
                                  h1: ({ children }) => <h1 className="text-xl font-bold mb-2">{children}</h1>,
                                  h2: ({ children }) => <h2 className="text-lg font-bold mb-2">{children}</h2>,
                                  h3: ({ children }) => <h3 className="text-base font-bold mb-1">{children}</h3>,
                                  a: ({ href, children }) => (
                                    <a href={href} className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">
                                      {children}
                                    </a>
                                  ),
                                }}
                              >
                                {part}
                              </ReactMarkdown>
                            );
                          })}
                        </div>
                      );
                    }
                    
                    // For customers or messages without images: Regular markdown rendering
                    return (
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
                          li: ({ children }) => <li className="mb-1">{children}</li>,
                          strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                          em: ({ children }) => <em className="italic">{children}</em>,
                          code: ({ node, inline, ...props }) =>
                            inline ? (
                              <code className="bg-gray-200 text-gray-800 px-1 py-0.5 rounded text-sm" {...props} />
                            ) : (
                              <code className="block bg-gray-200 text-gray-800 p-2 rounded text-sm my-2 overflow-x-auto" {...props} />
                            ),
                          h1: ({ children }) => <h1 className="text-xl font-bold mb-2">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-lg font-bold mb-2">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-base font-bold mb-1">{children}</h3>,
                          a: ({ href, children }) => (
                            <a href={href} className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">
                              {children}
                            </a>
                          ),
                        }}
                      >
                        {msg.message}
                      </ReactMarkdown>
                    );
                  })()}
                </div>
              )}
            </div>
          </div>
        ))}

        {(loading || followUpLoading) && (
          <div className="chat chat-start">
            <div className="chat-bubble chat-bubble-secondary">
              <span className="loading loading-dots loading-md"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white p-4 border-t-2 border-red-600">
        <div className="flex gap-2">
          <textarea
            className="textarea textarea-bordered flex-1 resize-none"
            placeholder="Type your message..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            rows="2"
            disabled={loading}
          />
          <button
            className="btn bg-red-600 hover:bg-red-700 text-white border-red-600"
            onClick={sendMessage}
            disabled={loading || !inputMessage.trim()}
          >
            {loading ? (
              <span className="loading loading-spinner"></span>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
                />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

