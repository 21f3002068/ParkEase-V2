// frontend/src/utils/auth.js

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
export function isAuthenticated() {
  const token = localStorage.getItem('auth-token');
  // Check if token exists and is not empty
  return !!(token && token.trim() !== '');
}

/**
 * Get user token from localStorage
 * @returns {string|null}
 */
export function getToken() {
  return localStorage.getItem('auth-token');
}

/**
 * Remove authentication token
 */
export function logout() {
  localStorage.removeItem('auth-token');
}

/**
 * Check if user has admin role
 * @returns {Promise<boolean>}
 */
export async function isAdmin() {
  const token = getToken();
  if (!token) return false;
  
  try {
    // Hit lightweight auth-check endpoint to verify admin role
    const response = await fetch('http://localhost:5000/api/admin/auth/check', {
      headers: { 'auth-token': token }
    });
    return response.ok;
  } catch (error) {
    console.error('Error checking admin role:', error);
    return false;
  }
}

/**
 * Check if user has user role
 * @returns {Promise<boolean>}
 */
export async function isUser() {
  const token = getToken();
  if (!token) return false;
  
  try {
    // Try to access user dashboard to verify user role
    const response = await fetch('http://localhost:5000/api/user/dashboard', {
      headers: { 'auth-token': token }
    });
    return response.ok;
  } catch (error) {
    console.error('Error checking user role:', error);
    return false;
  }
}