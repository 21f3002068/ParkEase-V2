<template>
  <div class="login-container">
    <form @submit.prevent="login">
      <h2>Welcome Back</h2>
      <p class="subtitle">Sign in to your ParkEase account</p>
      
      <label>
        Email Address
        <input v-model="username" type="email" required placeholder="Enter your email" />
      </label>
      <label>
        Password
        <input v-model="password" type="password" required placeholder="Enter your password" />
      </label>
      
      <div v-if="error" class="error">{{ error }}</div>
      
      <button type="submit">Sign In</button>
      
      <!-- Signup Link -->
      <div class="signup-link">
        <p>Don't have an account? 
          <router-link to="/signup" class="link">Sign up here</router-link>
        </p>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: "Login",
  data() {
    return {
      username: "",
      password: "",
      error: ""
    };
  },
  methods: {
    async login() {
      this.error = "";
      try {
        const formData = new URLSearchParams(); // builds a email=value&password=value string.
        formData.append('email', this.username);
        formData.append('password', this.password);

        const response = await fetch('http://localhost:5000/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData
        });
      
        const data = await response.json();
        console.log('Login response:', data); // Debug log

        if (response.ok && data.response && data.response.user && data.response.user.authentication_token) {
          localStorage.setItem('auth-token', data.response.user.authentication_token);

          // Check user role and redirect accordingly
          const userRoles = data.response.user.roles || [];
          if (userRoles.some(role => role.name === 'admin')) {
            this.$router.push('/admin');
          } else {
            this.$router.push('/user');
          }
        } else {
          this.error = data.response?.errors?.email?.[0] || data.response?.errors?.password?.[0] || data.message || "Invalid credentials";
        }
      } catch (err) {
        console.error('Login error:', err);
        this.error = "Server error. Please try again.";
      }
    }
  }
};
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  margin: 0;
}

.login-container h2 {
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

.login-container form {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  padding: 40px;
  width: 100%;
  max-width: 450px;
}

label {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

input {
  width: 100%;
  padding: 12px;
  margin-top: 8px;
  border: 2px solid #e1e5e9;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

input:focus {
  outline: none;
  border-color: #667eea;
}

button {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  margin-top: 10px;
}

button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.error {
  background-color: #fdf2f2;
  border: 1px solid #fca5a5;
  color: #dc2626;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
  margin-top: 12px;
}

.signup-link {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e1e5e9;
}

.signup-link p {
  color: #666;
  margin: 0;
}

.signup-link .link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.signup-link .link:hover {
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 600px) {
  .login-container {
    padding: 20px;
  }
  
  .login-container form {
    padding: 30px 20px;
  }
  
  .login-container h2 {
    font-size: 24px;
  }
}
</style>