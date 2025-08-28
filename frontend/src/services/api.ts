const API_URL = process.env.REACT_APP_API_URL || 'https://drinkswig.onrender.com';
const API_KEY = process.env.REACT_APP_API_KEY || 'ya5c6523a2dbf550e30c074fc0bf75fe6a669630c7dd141d1150bf064c884df64';

interface PaymentRequest {
  phone: string;
  amount: number;
}

interface PaymentResponse {
  payment_id: string;
  status: string;
  message: string;
}

interface PaymentStatusResponse {
  payment_id: string;
  status: string;
  amount: number;
  transaction_code?: string;
  created_at?: string;
}

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_URL}${endpoint}`;
  
  console.log('Making request to:', url); // Debug log
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`,
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    console.log('Response status:', response.status); // Debug log
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.log('Error data:', errorData); // Debug log
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status
      );
    }
    return await response.json();
  } catch (error) {
    console.log('Caught error:', error); // Debug log
    
    if (error instanceof ApiError) {
      throw error;
    }
    
    throw new ApiError(
      'Network error. Please check your connection and try again.'
    );
  }
};

export const initiatePayment = async (payment: PaymentRequest): Promise<PaymentResponse> => {
  return await apiRequest('/api/payments/initiate', {
    method: 'POST',
    body: JSON.stringify(payment),
  });
};

export const getPaymentStatus = async (paymentId: string): Promise<PaymentStatusResponse> => {
  return await apiRequest(`/api/payments/status/${paymentId}`);
};

export const getPaymentHistory = async (limit = 50, offset = 0) => {
  return await apiRequest(`/api/payments/history?limit=${limit}&offset=${offset}`);
};
