import React, { useState, useEffect } from 'react';
import PaymentForm from './components/PaymentForm';
import PaymentStatus from './components/PaymentStatus';
import './App.css';

interface PaymentState {
  paymentId: string | null;
  status: 'idle' | 'initiated' | 'pending' | 'success' | 'failed';
  amount: number;
  phone: string;
}

export default function App() {
  const [payment, setPayment] = useState<PaymentState>({
    paymentId: null,
    status: 'idle',
    amount: 0,
    phone: ''
  });

  const handlePaymentInitiated = (paymentId: string, amount: number, phone: string) => {
    setPayment({
      paymentId,
      status: 'initiated',
      amount,
      phone
    });
  };

  const handlePaymentStatusUpdate = (status: PaymentState['status']) => {
    setPayment(prev => ({ ...prev, status }));
  };

  const resetPayment = () => {
    setPayment({
      paymentId: null,
      status: 'idle',
      amount: 0,
      phone: ''
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              QR Payment System
            </h1>
            <p className="text-gray-600">
              Pay securely with M-Pesa
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            {payment.status === 'idle' ? (
              <PaymentForm 
                onPaymentInitiated={handlePaymentInitiated}
              />
            ) : (
              <PaymentStatus
                paymentId={payment.paymentId!}
                status={payment.status}
                amount={payment.amount}
                phone={payment.phone}
                onStatusUpdate={handlePaymentStatusUpdate}
                onReset={resetPayment}
              />
            )}
          </div>

          <div className="text-center mt-6 text-sm text-gray-500">
            <p>Powered by M-Pesa • Secure Payment Gateway</p>
          </div>
        </div>
      </div>
    </div>
  );
}