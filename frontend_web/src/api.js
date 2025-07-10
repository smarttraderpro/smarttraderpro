import axios from 'axios';

// The base URL will be proxied by React development server (setup in package.json "proxy")
// For production, this might be an environment variable or a relative path if served by the same backend.
const API_BASE_URL = '/api/v1'; // Matches FastAPI's API_V1_STR prefix

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add JWT token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API calls
export const loginUser = (credentials) => {
  return apiClient.post('/auth/login', credentials);
};

export const signupUser = (userData) => {
  return apiClient.post('/auth/signup', userData);
};

export const sendOtp = (identifier) => {
  return apiClient.post('/auth/send-otp', { identifier });
};

export const verifyOtp = (identifier, otp) => {
  return apiClient.post('/auth/verify-otp', { identifier, otp });
};


// User API calls
export const fetchUserProfile = () => {
  return apiClient.get('/users/me');
};

export const updateUserProfile = (profileData) => {
  return apiClient.put('/users/me', profileData);
};

export const updateUserBrokerCredentials = (credentialsData) => {
  return apiClient.put('/users/me/broker-credentials', credentialsData);
};


// Market Data API calls
export const fetchLiveIndices = () => {
  return apiClient.get('/market/live-indices');
};

// AngelOne Broker API calls
export const fetchAngelOneProfile = (pin, totp) => {
  const headers = {};
  if (pin) headers['X-Angelone-Pin'] = pin;
  if (totp) headers['X-Angelone-Totp'] = totp;
  return apiClient.get('/angelone/profile', { headers });
};

export const fetchAngelOneHoldings = (pin, totp) => {
  const headers = {};
  if (pin) headers['X-Angelone-Pin'] = pin;
  if (totp) headers['X-Angelone-Totp'] = totp;
  return apiClient.get('/angelone/holdings', { headers });
};


// Add other API functions as needed for different modules

export default apiClient; // Default export for general use if preferred
