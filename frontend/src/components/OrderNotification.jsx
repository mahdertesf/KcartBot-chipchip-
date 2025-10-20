import { useState } from 'react';
import { orderActionAPI } from '../utils/api';

const OrderNotification = ({ message, orderId, onActionComplete }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [showDeclineReason, setShowDeclineReason] = useState(false);
  const [declineReason, setDeclineReason] = useState('');
  const [actionTaken, setActionTaken] = useState(null);

  const handleAccept = async () => {
    if (!orderId) return;
    
    setIsProcessing(true);
    try {
      await orderActionAPI.acceptOrder(orderId);
      setActionTaken('accepted');
      onActionComplete && onActionComplete('accepted', orderId);
    } catch (error) {
      console.error('Error accepting order:', error);
      alert('Failed to accept order. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDecline = async () => {
    if (!orderId) return;
    
    setIsProcessing(true);
    try {
      await orderActionAPI.declineOrder(orderId, declineReason);
      setActionTaken('declined');
      onActionComplete && onActionComplete('declined', orderId);
    } catch (error) {
      console.error('Error declining order:', error);
      alert('Failed to decline order. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (actionTaken) {
    return (
      <div className="alert alert-success text-sm py-2">
        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Order {actionTaken} successfully!</span>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-3">
        <div dangerouslySetInnerHTML={{ __html: message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>') }} />
      </div>
      
      {orderId && (
        <div className="flex flex-col gap-2 mt-3">
          {!showDeclineReason ? (
            <div className="flex gap-2">
              <button 
                className="btn btn-success btn-sm flex-1"
                onClick={handleAccept}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <span className="loading loading-spinner loading-xs"></span>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                    </svg>
                    Accept
                  </>
                )}
              </button>
              <button 
                className="btn btn-error btn-sm flex-1"
                onClick={() => setShowDeclineReason(true)}
                disabled={isProcessing}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
                Decline
              </button>
            </div>
          ) : (
            <div className="w-full">
              <textarea 
                className="textarea textarea-bordered textarea-sm w-full text-black bg-white"
                placeholder="Reason for declining (optional)..."
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                rows="2"
              />
              <div className="flex gap-2 mt-2">
                <button 
                  className="btn btn-error btn-sm flex-1"
                  onClick={handleDecline}
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <span className="loading loading-spinner loading-xs"></span>
                  ) : (
                    'Confirm Decline'
                  )}
                </button>
                <button 
                  className="btn btn-ghost btn-sm flex-1"
                  onClick={() => setShowDeclineReason(false)}
                  disabled={isProcessing}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OrderNotification;


