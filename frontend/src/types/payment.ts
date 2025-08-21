export interface Payment {
  id?: number;
  payment_id: string;
  phone_number: string;
  amount: number;
  status: 'pending' | 'success' | 'failed';
  transaction_code?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PaymentRequest {
  phone: string;
  amount: number;
}

export interface PaymentInitiateResponse {
  payment_id: string;
  status: string;
  message: string;
}

export interface PaymentStatusResponse {
  payment_id: string;
  status: string;
  amount: number;
  transaction_code?: string;
  created_at?: string;
}