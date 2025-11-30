<template>
  <div class="signup-container">
    <div class="signup-card">
      <h2>Create Account</h2>
      <p class="subtitle">Join ParkEase to find and book parking spots</p>
      
      <form @submit.prevent="signup" class="signup-form">
        <!-- Email -->
        <div class="form-group">
          <label for="email">Email Address *</label>
          <input 
            id="email"
            v-model="formData.email" 
            type="email" 
            required 
            :class="{ 'error': errors.email, 'checking': checkingEmail }"
            @input="onEmailChange"
            @blur="checkAvailability('email')"
          />
          <span v-if="checkingEmail" class="checking-message">Checking availability...</span>
          <span v-if="errors.email" class="error-message">{{ errors.email[0] }}</span>
          <span v-if="emailAvailable === true" class="success-message">Email is available!</span>
        </div>

        <!-- Password -->
        <div class="form-group">
          <label for="password">Password *</label>
          <input 
            id="password"
            v-model="formData.password" 
            type="password" 
            required 
            :class="{ 'error': errors.password }"
            @input="clearError('password')"
          />
          <span v-if="errors.password" class="error-message">{{ errors.password[0] }}</span>
          <div class="password-requirements">
            <small>Password must be at least 6 characters long</small>
          </div>
        </div>

        <!-- Confirm Password -->
        <div class="form-group">
          <label for="confirm_password">Confirm Password *</label>
          <input 
            id="confirm_password"
            v-model="formData.confirm_password" 
            type="password" 
            required 
            :class="{ 'error': errors.confirm_password }"
            @input="clearError('confirm_password')"
          />
          <span v-if="errors.confirm_password" class="error-message">{{ errors.confirm_password[0] }}</span>
        </div>

        <!-- General Error -->
        <div v-if="errors.general" class="general-error">
          {{ errors.general[0] }}
        </div>

        <!-- Submit Button -->
        <button 
          type="submit" 
          class="signup-btn"
          :disabled="isLoading || !isFormValid"
        >
          {{ isLoading ? 'Creating Account...' : 'Create Account' }}
        </button>
      </form>

      <!-- Login Link -->
      <div class="login-link">
        <p>Already have an account? 
          <router-link to="/login" class="link">Sign in here</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Signup",
  data() {
    return {
      formData: {
        email: '',
        password: '',
        confirm_password: ''
      },
      errors: {},
      isLoading: false,
      checkingEmail: false,
      emailAvailable: null,
      emailTimeout: null
    }
  },
  
  computed: {
    isFormValid() {
      return this.formData.email && 
             this.formData.password && 
             this.formData.confirm_password &&
             this.formData.password === this.formData.confirm_password &&
             this.formData.password.length >= 6 &&
             Object.keys(this.errors).length === 0;
    }
  },

  methods: {
    async signup() {
      this.isLoading = true;
      this.errors = {};
      
      try {
        const response = await fetch('http://localhost:5000/api/signup', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.formData)
        });

        const data = await response.json();

        if (response.ok && data.response && data.response.user) {
          // Show success message
          this.$toast?.success?.(data.message || 'Account created successfully! Please login to continue.');

          // Redirect to login page for authentication
          setTimeout(() => {
            this.$router.push('/login');
          }, 2000); // Give user time to read the success message
        } else {
          // Handle validation errors
          if (data.response && data.response.errors) {
            this.errors = data.response.errors;
          } else {
            this.errors = { general: [data.message || 'Registration failed'] };
          }
        }
      } catch (error) {
        console.error('Signup error:', error);
        this.errors = { general: ['Server error. Please try again.'] };
      } finally {
        this.isLoading = false;
      }
    },

    async checkAvailability(field) {
      const value = this.formData[field];
      if (!value || value.length < 3) return;

      this.checkingEmail = true;
      this.emailAvailable = null;

      try {
        const response = await fetch('http://localhost:5000/api/check-availability', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ field, value })
        });

        const data = await response.json();

        this.emailAvailable = data.available;
        if (!data.available) {
          this.errors = { ...this.errors, email: ['Email already registered'] };
        }
      } catch (error) {
        console.error('Availability check error:', error);
      } finally {
        this.checkingEmail = false;
      }
    },

    onEmailChange() {
      this.clearError('email');
      this.emailAvailable = null;
      
      // Debounce availability check
      clearTimeout(this.emailTimeout);
      this.emailTimeout = setTimeout(() => {
        if (this.formData.email && this.formData.email.includes('@')) {
          this.checkAvailability('email');
        }
      }, 500);
    },

    clearError(field) {
      if (this.errors[field]) {
        const newErrors = { ...this.errors };
        delete newErrors[field];
        this.errors = newErrors;
      }
    }
  },

  beforeUnmount() {
    clearTimeout(this.emailTimeout);
  }
}
</script>

<style scoped>
.signup-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  margin: 0;
}

.signup-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  padding: 40px;
  width: 100%;
  max-width: 500px;
}

.signup-card h2 {
  text-align: center;
  color: #333;
  margin-bottom: 8px;
  font-size: 28px;
  font-weight: 600;
}

.subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 30px;
  font-size: 16px;
}

.signup-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-group input {
  padding: 12px;
  border: 2px solid #e1e5e9;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input.error {
  border-color: #e74c3c;
}

.form-group input.checking {
  border-color: #f39c12;
}

.error-message {
  color: #e74c3c;
  font-size: 12px;
  margin-top: 4px;
}

.success-message {
  color: #27ae60;
  font-size: 12px;
  margin-top: 4px;
}

.checking-message {
  color: #f39c12;
  font-size: 12px;
  margin-top: 4px;
}

.password-requirements {
  margin-top: 4px;
}

.password-requirements small {
  color: #666;
  font-size: 12px;
}

.general-error {
  background-color: #fdf2f2;
  border: 1px solid #fca5a5;
  color: #dc2626;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
}

.signup-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 14px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  margin-top: 10px;
}

.signup-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.signup-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e1e5e9;
}

.login-link p {
  color: #666;
  margin: 0;
}

.login-link .link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.login-link .link:hover {
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 600px) {
  .signup-container {
    padding: 20px;
  }
  
  .signup-card {
    padding: 30px 20px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .signup-card h2 {
    font-size: 24px;
  }
}
</style>