import React, { useState } from 'react';
import { initiatePayment } from '../services/api';

interface PaymentFormProps {
  onPaymentInitiated: (paymentId: string, amount: number, phone: string) => void;
}

const PaymentForm: React.FC<PaymentFormProps> = ({ onPaymentInitiated }) => {
  const [phone, setPhone] = useState('254');
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const validatePhone = (phoneNumber: string): boolean => {
    const phonePattern = /^254[0-9]{9}$/;
    return phonePattern.test(phoneNumber);
  };

  const validateAmount = (amountStr: string): boolean => {
    const amt = parseFloat(amountStr);
    return amt >= 1 && amt <= 100000;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!validatePhone(phone)) {
      setError('Please enter a valid phone number (254XXXXXXXXX)');
      return;
    }

    if (!validateAmount(amount)) {
      setError('Amount must be between KES 1 and KES 100,000');
      return;
    }

    setLoading(true);

    try {
      const response = await initiatePayment({
        phone,
        amount: parseFloat(amount)
      });

      if (response.payment_id) {
        onPaymentInitiated(response.payment_id, parseFloat(amount), phone);
      } else {
        throw new Error(response.message || 'Failed to initiate payment');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to initiate payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
          M-Pesa Phone Number
        </label>
        <input
          type="tel"
          id="phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="254712345678"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          maxLength={12}
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          Enter your M-Pesa number (format: 254XXXXXXXXX)
        </p>
      </div>

      <div>
        <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-2">
          Amount (KES)
        </label>
        <input
          type="number"
          id="amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="100"
          min="1"
          max="100000"
          step="0.01"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          Enter amount between KES 1 and KES 100,000
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            Initiating Payment...
          </div>
        ) : (
          'Pay with M-Pesa'
        )}
      </button>

      <div className="text-center">
        <p className="text-xs text-gray-500">
          You will receive an STK push notification on your phone
        </p>
      </div>
    </form>
  );
};

export default PaymentForm;