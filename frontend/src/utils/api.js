// API utility functions
const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:5000/api';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

// Generic API request function
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('auth-token');

  // Add cache busting query parameter instead of headers
  const cacheBuster = `_t=${Date.now()}`;
  const separator = endpoint.includes('?') ? '&' : '?';
  const urlWithCacheBuster = `${API_BASE_URL}${endpoint}${separator}${cacheBuster}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'auth-token': token }),
      ...options.headers
    },
    ...options
  };

  try {
    const response = await fetch(urlWithCacheBuster, config);
    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(data.error || 'Request failed', response.status, data);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Network error occurred', 0, null);
  }
}

// CRUD operations factory
export function createCrudApi(baseEndpoint) {
  return {
    async getAll() {
      return apiRequest(baseEndpoint);
    },

    async getById(id) {
      return apiRequest(`${baseEndpoint}/${id}`);
    },

    async create(data) {
      return apiRequest(baseEndpoint, {
        method: 'POST',
        body: JSON.stringify(data)
      });
    },

    async update(id, data) {
      return apiRequest(`${baseEndpoint}/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
      });
    },

    async delete(id) {
      return apiRequest(`${baseEndpoint}/${id}`, {
        method: 'DELETE'
      });
    }
  };
}

// Specific API endpoints
export const userApi = {
  // Profile
  getProfile: () => apiRequest('/user/profile'),
  updateProfile: (data) => apiRequest('/user/profile', {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  deleteAccount: (data) => apiRequest('/user/delete-account', {
    method: 'DELETE',
    body: JSON.stringify(data)
  }),

  // Bookings/Reservations
  getReservations: () => apiRequest('/user/my_reservations'),
  bookSpot: (lotId, data) => apiRequest(`/user/book/${lotId}`, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  getBookingData: (lotId) => apiRequest(`/user/booking_data/${lotId}`),
  parkIn: (reservationId) => apiRequest(`/user/park/${reservationId}`, {
    method: 'POST'
  }),
  parkOut: (reservationId) => apiRequest(`/user/park_out/${reservationId}`, {
    method: 'POST'
  }),

  // Vehicles
  getVehicles: () => apiRequest('/user/my_vehicles'),
  addVehicle: (data) => apiRequest('/user/add_vehicle', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  updateVehicle: (id, data) => apiRequest(`/user/update_vehicle/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  deleteVehicle: (id) => apiRequest(`/user/remove_vehicle/${id}`, {
    method: 'DELETE'
  }),

  // Parking Lots
  getParkingLots: () => apiRequest('/user/parking_lots'),
  searchParkingLots: (query) => apiRequest(`/user/search?query=${encodeURIComponent(query)}`),

  // Analytics
  getAnalytics: () => apiRequest('/user/analytics/dashboard'),

  // Favorites
  getFavorites: () => apiRequest('/user/favorites'),
  toggleFavorite: (lotId, isFavorite) => apiRequest(`/user/favorites/${lotId}`, {
    method: isFavorite ? 'DELETE' : 'POST'
  }),

  // CSV Export
  exportCSV: () => apiRequest('/user/export', { method: 'POST' })
};

export { ApiError };