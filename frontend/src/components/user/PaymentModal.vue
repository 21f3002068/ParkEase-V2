<template>
  <div v-if="show" class="modal-overlay" @click.self="closeModal">
    <div class="payment-modal">
      <div class="modal-header">
        <h2><i class="fas fa-credit-card"></i> Complete Payment</h2>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>

      <div class="modal-body">
        <!-- Payment Summary -->
        <div class="payment-summary">
          <h3>Payment Summary</h3>
          <div class="summary-row">
            <span>Booking ID:</span>
            <strong>{{ bookingId }}</strong>
          </div>
          <div class="summary-row">
            <span>Parking Duration:</span>
            <strong>{{ formattedDuration }}</strong>
          </div>
          <div class="summary-row total">
            <span>Total Amount:</span>
            <strong class="amount">₹{{ amount }}</strong>
          </div>
        </div>

        <!-- Payment Method Selection -->
        <div class="payment-methods">
          <h3>Select Payment Method</h3>
          <div class="method-grid">
            <div 
              v-for="method in paymentMethods" 
              :key="method.id"
              :class="['method-card', { selected: selectedMethod === method.id }]"
              @click="selectMethod(method.id)"
            >
              <i :class="method.icon"></i>
              <span>{{ method.name }}</span>
              <div v-if="selectedMethod === method.id" class="check-mark">
                <i class="fas fa-check-circle"></i>
              </div>
            </div>
          </div>
        </div>

        <!-- Payment Details (if UPI or Card selected) -->
        <div v-if="selectedMethod === 'upi' || selectedMethod === 'card'" class="payment-details">
          <div v-if="selectedMethod === 'upi'" class="upi-section">
            <h4>UPI Payment</h4>
            <p class="instruction">Scan the QR code or use UPI ID to pay</p>
            <div class="qr-placeholder">
              <i class="fas fa-qrcode"></i>
              <p>QR Code</p>
            </div>
            <div class="upi-id">
              <strong>UPI ID:</strong> parkease@upi
            </div>
            <input 
              v-model="transactionId" 
              type="text" 
              placeholder="Enter UPI Transaction ID (optional)"
              class="transaction-input"
            />
          </div>

          <div v-if="selectedMethod === 'card'" class="card-section">
            <h4>Card Payment</h4>
            <p class="instruction">Enter your card details</p>
            <input 
              v-model="cardNumber" 
              type="text" 
              placeholder="Card Number"
              maxlength="19"
              class="card-input"
            />
            <div class="card-row">
              <input 
                v-model="expiryDate" 
                type="text" 
                placeholder="MM/YY"
                maxlength="5"
                class="card-input half"
              />
              <input 
                v-model="cvv" 
                type="text" 
                placeholder="CVV"
                maxlength="3"
                class="card-input half"
              />
            </div>
            <input 
              v-model="cardholderName" 
              type="text" 
              placeholder="Cardholder Name"
              class="card-input"
            />
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="error-message">
          <i class="fas fa-exclamation-circle"></i>
          {{ error }}
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary" :disabled="processing">
          Cancel
        </button>
        <button 
          @click="processPayment" 
          class="btn-primary" 
          :disabled="!selectedMethod || processing"
        >
          <i v-if="processing" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-check"></i>
          {{ processing ? 'Processing...' : `Pay ₹${amount}` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PaymentModal',
  props: {
    show: {
      type: Boolean,
      required: true
    },
    reservationId: {
      type: Number,
      required: true
    },
    bookingId: {
      type: String,
      required: true
    },
    amount: {
      type: Number,
      required: true
    },
    durationHours: {
      type: Number,
      default: 0
    }
  },
  data() {
    return {
      selectedMethod: null,
      transactionId: '',
      cardNumber: '',
      expiryDate: '',
      cvv: '',
      cardholderName: '',
      processing: false,
      error: null,
      paymentMethods: [
        { id: 'upi', name: 'UPI', icon: 'fas fa-mobile-alt' },
        { id: 'card', name: 'Credit/Debit Card', icon: 'fas fa-credit-card' },
        { id: 'cash', name: 'Cash', icon: 'fas fa-money-bill-wave' }
      ]
    }
  },
  computed: {
    formattedDuration() {
      const totalHours = this.durationHours;
      
      if (totalHours === 0) {
        return '0 minutes';
      }
      
      const hours = Math.floor(totalHours);
      const minutes = Math.floor((totalHours - hours) * 60);
      const seconds = Math.floor(((totalHours - hours) * 60 - minutes) * 60);
      
      const parts = [];
      if (hours > 0) parts.push(`${hours}h`);
      if (minutes > 0) parts.push(`${minutes}m`);
      if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);
      
      return parts.join(' ');
    }
  },
  methods: {
    selectMethod(methodId) {
      this.selectedMethod = methodId;
      this.error = null;
    },

    async processPayment() {
      if (!this.selectedMethod) {
        this.error = 'Please select a payment method';
        return;
      }

      // Validate card details if card payment
      if (this.selectedMethod === 'card') {
        if (!this.cardNumber || !this.expiryDate || !this.cvv || !this.cardholderName) {
          this.error = 'Please fill in all card details';
          return;
        }
      }

      this.processing = true;
      this.error = null;

      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/user/payments/process', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          },
          body: JSON.stringify({
            reservation_id: this.reservationId,
            payment_method: this.selectedMethod.toUpperCase(),
            transaction_id: this.transactionId || null
          })
        });

        const data = await response.json();

        if (response.ok) {
          this.$emit('payment-success', data);
          this.closeModal();
        } else {
          this.error = data.error || 'Payment failed. Please try again.';
        }
      } catch (err) {
        console.error('Payment error:', err);
        this.error = 'Network error. Please check your connection and try again.';
      } finally {
        this.processing = false;
      }
    },

    closeModal() {
      if (!this.processing) {
        this.$emit('close');
      }
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.payment-modal {
  background: white;
  border-radius: 16px;
  width: 90%;
  max-width: 550px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px 16px 0 0;
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.modal-header h2 i {
  margin-right: 10px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  color: white;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: 24px;
}

.payment-summary {
  background: #f9fafb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.payment-summary h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #374151;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  color: #6b7280;
}

.summary-row.total {
  border-top: 2px solid #e5e7eb;
  margin-top: 12px;
  padding-top: 16px;
  font-size: 18px;
  color: #111827;
}

.summary-row .amount {
  color: #10b981;
  font-size: 24px;
}

.payment-methods h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #374151;
}

.method-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.method-card {
  position: relative;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.method-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.method-card.selected {
  border-color: #667eea;
  background: #f0f4ff;
}

.method-card i {
  font-size: 32px;
  color: #667eea;
  margin-bottom: 8px;
}

.method-card span {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.check-mark {
  position: absolute;
  top: 8px;
  right: 8px;
  color: #10b981;
  font-size: 20px;
}

.payment-details {
  background: #f9fafb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.payment-details h4 {
  margin: 0 0 8px 0;
  color: #374151;
}

.instruction {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 16px;
}

.qr-placeholder {
  background: white;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  margin-bottom: 16px;
}

.qr-placeholder i {
  font-size: 80px;
  color: #9ca3af;
}

.qr-placeholder p {
  margin: 12px 0 0 0;
  color: #6b7280;
}

.upi-id {
  background: white;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  margin-bottom: 16px;
  color: #374151;
}

.transaction-input,
.card-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.transaction-input:focus,
.card-input:focus {
  outline: none;
  border-color: #667eea;
}

.card-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 12px 0;
}

.card-input.half {
  width: 100%;
}

.error-message {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #dc2626;
  padding: 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

@media (max-width: 600px) {
  .payment-modal {
    width: 95%;
    max-height: 95vh;
  }

  .method-grid {
    grid-template-columns: 1fr;
  }
}
</style>
