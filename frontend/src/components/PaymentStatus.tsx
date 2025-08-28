import React, { useState, useEffect } from 'react';
import { getPaymentStatus } from '../services/api';

interface PaymentStatusProps {
  paymentId: string;
  status: 'idle' | 'initiated' | 'pending' | 'success' | 'failed'; // ✅ Specific union
  amount: number;
  phone: string;
  onStatusUpdate: (status: 'idle' | 'initiated' | 'pending' | 'success' | 'failed') => void; // ✅ Match exact type
  onReset: () => void;
}

const PaymentStatus: React.FC<PaymentStatusProps> = ({
  paymentId,
  status,
  amount,
  phone,
  onStatusUpdate,
  onReset
}) => {
  const [transactionCode, setTransactionCode] = useState('');
  const [polling, setPolling] = useState(true);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (polling && (status === 'initiated' || status === 'pending')) {
      interval = setInterval(async () => {
        try {
          const response = await getPaymentStatus(paymentId);
          
          if (response.status !== status) {
            onStatusUpdate(response.status as 'idle' | 'initiated' | 'pending' | 'success' | 'failed');
            
            if (response.status === 'success') {
              setTransactionCode(response.transaction_code || '');
              setPolling(false);
              
              // Redirect to WhatsApp after 3 seconds
              setTimeout(() => {
                const whatsappUrl = `https://wa.me/254724577131?text=Hi%2C%20I%27ve%20just%20paid%20KES%20${amount}%20for%20the%20kombucha%20order.%20Transaction%20Code%3A%20${response.transaction_code}%20Phone%3A%20${phone}`;
                window.location.href = whatsappUrl;
              }, 3000);
              
            } else if (response.status === 'failed') {
              setPolling(false);
            }
          }
        } catch (error) {
          console.error('Error checking payment status:', error);
        }
      }, 3000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [paymentId, status, polling, onStatusUpdate, amount, phone]);

  const getStatusIcon = () => {
    switch (status) {
      case 'initiated':
      case 'pending':
        return (
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        );
      case 'success':
        return (
          <div className="rounded-full h-12 w-12 bg-green-100 flex items-center justify-center mx-auto">
            <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
        );
      case 'failed':
        return (
          <div className="rounded-full h-12 w-12 bg-red-100 flex items-center justify-center mx-auto">
            <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  const getStatusMessage = () => {
    switch (status) {
      case 'initiated':
        return {
          title: 'Payment Initiated',
          message: 'Please check your phone for the M-Pesa STK push notification and enter your PIN to complete the payment.',
          color: 'text-blue-600'
        };
      case 'pending':
        return {
          title: 'Processing Payment',
          message: 'We are processing your payment. Please wait...',
          color: 'text-yellow-600'
        };
      case 'success':
        return {
          title: 'Payment Successful!',
          message: 'Your payment has been processed successfully. You will be redirected to WhatsApp shortly.',
          color: 'text-green-600'
        };
      case 'failed':
        return {
          title: 'Payment Failed',
          message: 'Your payment could not be processed. Please try again.',
          color: 'text-red-600'
        };
      default:
        return {
          title: 'Unknown Status',
          message: 'Please contact support.',
          color: 'text-gray-600'
        };
    }
  };

  const statusInfo = getStatusMessage();

  return (
    <div className="text-center space-y-6">
      {getStatusIcon()}
      
      <div>
        <h2 className={`text-xl font-semibold ${statusInfo.color} mb-2`}>
          {statusInfo.title}
        </h2>
        <p className="text-gray-600">
          {statusInfo.message}
        </p>
      </div>

      <div className="bg-gray-50 rounded-md p-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Amount:</span>
          <span className="font-medium">KES {amount.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Phone:</span>
          <span className="font-medium">{phone}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Payment ID:</span>
          <span className="font-mono text-xs">{paymentId.slice(0, 8)}...</span>
        </div>
        {transactionCode && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Transaction Code:</span>
            <span className="font-mono text-xs text-green-600">{transactionCode}</span>
          </div>
        )}
      </div>

      {status === 'success' && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <p className="text-sm text-green-700">
            🎉 Redirecting to WhatsApp in 3 seconds...
          </p>
        </div>
      )}

      {status === 'failed' && (
        <button
          onClick={onReset}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

export default PaymentStatus;
