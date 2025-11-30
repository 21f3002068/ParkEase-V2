import { createRouter, createWebHistory } from 'vue-router';
import { isAuthenticated, isAdmin, isUser } from '../utils/auth.js';

import AdminDashboard from '../views/admin/AdminDashboard.vue';
import ManageLots from '../components/admin/ManageLots.vue';

import UserDashboard from '../views/user/UserDashboard.vue';
import BookParking from '../components/user/BookParking.vue';

// Import the Login and Signup pages
import Login from '../views/login.vue';
import Signup from '../views/signup.vue';

const routes = [
  {
    path: '/login',
    component: Login,
    meta: { requiresGuest: true } // Only accessible when not logged in
  },
  {
    path: '/signup',
    component: Signup,
    meta: { requiresGuest: true } // Only accessible when not logged in
  },
  {
    path: '/admin',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/manage',
    component: ManageLots,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/user',
    component: UserDashboard,
    meta: { requiresAuth: true, requiresUser: true }
  },
  {
    path: '/user/book',
    component: BookParking,
    meta: { requiresAuth: true, requiresUser: true }
  },
  {
    path: '/',
    redirect: '/login' // Redirect to login by default
  },
  {
    path: '/:pathMatch(.*)*', // Catch all unmatched routes
    redirect: '/login'
  }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
});

// Global navigation guard
router.beforeEach(async (to, from, next) => {
  console.log('Navigating to:', to.path);

  // Handle root path redirect
  if (to.path === '/') {
    next('/login');
    return;
  }

  // Handle login and signup page access
  if (to.path === '/login' || to.path === '/signup') {
    // Always allow access to login/signup pages, but redirect if already authenticated
    const hasToken = isAuthenticated();
    if (hasToken) {
      try {
        // Check admin first, then user if not admin
        const adminRole = await isAdmin();
        if (adminRole) {
          next('/admin');
          return;
        }
        
        const userRole = await isUser();
        if (userRole) {
          next('/user');
          return;
        }
        
        // Token exists but invalid, clear it and allow access to login/signup
        localStorage.removeItem('auth-token');
      } catch (error) {
        // Error checking roles, clear token
        localStorage.removeItem('auth-token');
      }
    }
    // Allow access to login/signup pages
    next();
    return;
  }

  // Handle protected routes
  if (to.path.startsWith('/admin') || to.path.startsWith('/user')) {
    const hasToken = isAuthenticated();

    if (!hasToken) {
      // No token, redirect to login
      next('/login');
      return;
    }

    try {
      if (to.path.startsWith('/admin')) {
        // Admin route - check admin role only
        const adminRole = await isAdmin();
        if (adminRole) {
          next();
          return;
        }
        
        // Not admin, check if they're a regular user
        const userRole = await isUser();
        if (userRole) {
          // User trying to access admin, redirect to user dashboard
          next('/user');
          return;
        }
        
        // No valid role, clear token and redirect to login
        localStorage.removeItem('auth-token');
        next('/login');
        return;
      }

      if (to.path.startsWith('/user')) {
        // User route - check user role first, then admin (admins can access user routes)
        const userRole = await isUser();
        if (userRole) {
          next();
          return;
        }
        
        // Not a user, check if they're admin
        const adminRole = await isAdmin();
        if (adminRole) {
          next();
          return;
        }
        
        // No valid role, clear token and redirect to login
        localStorage.removeItem('auth-token');
        next('/login');
        return;
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      localStorage.removeItem('auth-token');
      next('/login');
      return;
    }
  }

  // For any other routes, allow access
  next();
});

// This router configuration sets up protected routes with proper authentication guards