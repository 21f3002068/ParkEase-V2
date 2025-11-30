<template>
  <div class="parking-visualizer">
    <!-- Status Legend -->
    <div class="status-legend">
      <div class="legend-item">
        <div class="status-box available"></div>
        <span>Available</span>
      </div>
      <div class="legend-item">
        <div class="status-box booked"></div>
        <span>Booked</span>
      </div>
      <div class="legend-item">
        <div class="status-box occupied"></div>
        <span>Occupied</span>
      </div>
      <div class="legend-item">
        <div class="status-box unavailable"></div>
        <span>Unavailable</span>
      </div>
      <div class="legend-item">
        <div class="status-box inactive-lot-legend"></div>
        <span>Inactive Lot</span>
      </div>
    </div>

    <!-- Parking Lots Grid -->
    <div class="parking-lots-grid">
      <!-- Add New Parking Lot Card - First Position -->
      <div class="parking-lot-card add-lot-card" @click="$emit('add-lot')">
        <div class="add-lot-content">
          <i class="fas fa-plus add-icon"></i>
          <span>Add New Parking Lot</span>
        </div>
      </div>

      <div v-for="lot in parkingLots" :key="lot.id" class="parking-lot-card" :class="{ 'inactive-lot': !lot.isActive }">
        <div class="lot-header">
          <h3>{{ lot.name }}</h3>
          <div class="lot-status">{{ lot.occupiedSpots }} / {{ lot.totalSpots }}</div>
          <button class="menu-button" @click="showLotMenu(lot)">⋮</button>
        </div>

        <div class="parking-slots">
          <div v-for="spot in lot.spots" :key="spot.id" class="parking-slot" :class="getSpotStatusClass(spot)"
            @click="showSpotDetails(spot, lot)"></div>
        </div>

        <!-- Toggle Button -->
        <button 
          class="toggle-button" 
          :class="{ 'active': lot.isActive, 'inactive': !lot.isActive }"
          @click="toggleLotStatus(lot)"
          :title="lot.isActive ? 'Deactivate parking lot' : 'Activate parking lot'"
        >
          <i :class="lot.isActive ? 'fas fa-toggle-on' : 'fas fa-toggle-off'"></i>
        </button>
      </div>
    </div>

    <!-- Floating Add Button -->
    <button class="floating-add-btn" @click="$emit('add-lot')" title="Add New Parking Lot">
      <i class="fas fa-plus"></i>
    </button>

    <!-- Spot Details Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>Parking Spot Details</h3>
          <button class="close-button" @click="closeModal">×</button>
        </div>

        <div class="modal-content">
          <div class="spot-info">
            <p><strong>Lot:</strong> {{ selectedLot.name }}</p>
            <p><strong>Spot ID:</strong> {{ selectedSpot.id }}</p>
            <p><strong>Status:</strong> <span :class="'status-' + selectedSpot.status">{{
              getStatusText(selectedSpot.status) }}</span></p>
          </div>

          <div v-if="selectedSpot.status === 'O' && currentReservation.id" class="current-reservation">
            <h4><i class="fas fa-car"></i> Current Reservation</h4>
            <div class="reservation-details">
              <div class="detail-row">
                <span class="label">Reservation ID:</span>
                <span class="value">{{ currentReservation.booking_id || '#' + currentReservation.id }}</span>
              </div>
              <div class="detail-row">
                <span class="label">User:</span>
                <span class="value">{{ currentReservation.user_name }} ({{ currentReservation.username }})</span>
              </div>
              <div class="detail-row">
                <span class="label">Email:</span>
                <span class="value">{{ currentReservation.email }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Vehicle:</span>
                <span class="value">{{ currentReservation.vehicle_plate }} - {{ currentReservation.vehicle_model }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Check-in Time:</span>
                <span class="value">{{ formatDateTime(currentReservation.parking_timestamp) }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Duration:</span>
                <span class="value">{{ calculateDuration(currentReservation.parking_timestamp) }}</span>
              </div>
              <div class="detail-row" v-if="currentReservation.expected_departure">
                <span class="label">Expected Departure:</span>
                <span class="value">{{ formatDateTime(currentReservation.expected_departure) }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Status:</span>
                <span class="value status-badge status-active">{{ currentReservation.status }}</span>
              </div>
              <div class="detail-row" v-if="currentReservation.parking_cost">
                <span class="label">Current Cost:</span>
                <span class="value cost-value">₹{{ currentReservation.parking_cost }}</span>
              </div>
            </div>
          </div>

          <div v-if="selectedSpot.status === 'B'" class="upcoming-reservations">
            <h4><i class="fas fa-calendar-check"></i> Booked Reservation</h4>
            <div v-if="upcomingReservations.length === 0" class="no-data-message">
              <p>No reservation details found for this booked spot.</p>
              <p class="hint">The spot may be marked as booked but doesn't have an active reservation.</p>
            </div>
            <div v-for="(res, index) in upcomingReservations" :key="index" class="reservation-details">
              <div class="detail-row">
                <span class="label">Reservation ID:</span>
                <span class="value">{{ res.booking_id || '#' + res.id }}</span>
              </div>
              <div class="detail-row">
                <span class="label">User:</span>
                <span class="value">{{ res.user_name }} ({{ res.username }})</span>
              </div>
              <div class="detail-row">
                <span class="label">Email:</span>
                <span class="value">{{ res.email }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Vehicle:</span>
                <span class="value">{{ res.vehicle_plate }} - {{ res.vehicle_model }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Booking Time:</span>
                <span class="value">{{ formatDateTime(res.booking_timestamp) }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Expected Arrival:</span>
                <span class="value">{{ formatDateTime(res.expected_arrival) }}</span>
              </div>
              <div class="detail-row" v-if="res.expected_departure">
                <span class="label">Expected Departure:</span>
                <span class="value">{{ formatDateTime(res.expected_departure) }}</span>
              </div>
              <div class="detail-row">
                <span class="label">Status:</span>
                <span class="value status-badge status-confirmed">{{ res.status }}</span>
              </div>
            </div>
          </div>

          <div v-if="selectedSpot.status === 'O' && !currentReservation.id && !currentReservation.error" class="loading-state">
            <i class="fas fa-spinner fa-spin"></i> Loading reservation details...
          </div>

          <div v-if="currentReservation.error" class="error-state">
            <i class="fas fa-exclamation-circle"></i>
            <p>{{ currentReservation.error }}</p>
          </div>

          <div class="spot-actions">
            <button v-if="selectedSpot.status === 'A'" class="action-button mark-unavailable"
              @click="updateSpotStatus('X')">
              Mark as Unavailable
            </button>
            <button v-if="selectedSpot.status === 'X'" class="action-button mark-available"
              @click="updateSpotStatus('A')">
              Mark as Available
            </button>
            <button v-if="selectedSpot.status === 'O'" class="action-button force-release" @click="forceReleaseSpot">
              Force Release
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ParkingLotVisualizer',
  props: {
    parkingLots: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      showModal: false,
      selectedSpot: null,
      selectedLot: null,
      currentReservation: {},
      upcomingReservations: []
    };
  },
  methods: {
    getSpotStatusClass(spot) {
      switch (spot.status) {
        case 'A': return 'available';
        case 'B': return 'booked';
        case 'O': return 'occupied';
        case 'X': return 'unavailable';
        default: return 'available';
      }
    },
    getStatusText(status) {
      switch (status) {
        case 'A': return 'Available';
        case 'B': return 'Booked';
        case 'O': return 'Occupied';
        case 'X': return 'Unavailable';
        default: return 'Unknown';
      }
    },
    showLotMenu(lot) {
      this.$emit('lot-menu', lot);
    },
    async showSpotDetails(spot, lot) {
      this.selectedSpot = spot;
      this.selectedLot = lot;
      this.showModal = true;
      
      // Reset data
      this.currentReservation = {};
      this.upcomingReservations = [];

      // Fetch current reservation if spot is occupied
      if (spot.status === 'O') {
        await this.fetchCurrentReservation(spot.id);
      }

      // Fetch upcoming reservations for booked spots or any spot
      if (spot.status === 'B' || spot.status === 'O') {
        await this.fetchUpcomingReservations(spot.id);
      }
    },
    closeModal() {
      this.showModal = false;
      this.selectedSpot = null;
      this.selectedLot = null;
      this.currentReservation = {};
      this.upcomingReservations = [];
    },
    async fetchCurrentReservation(spotId) {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/spots/${spotId}/current-reservation`, {
          headers: { 'auth-token': token }
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Current reservation data:', data);
          this.currentReservation = data;
        } else {
          const errorData = await response.json();
          console.error('Failed to fetch current reservation:', errorData);
          this.currentReservation = { error: errorData.error || 'Failed to load' };
        }
      } catch (err) {
        console.error('Error fetching current reservation:', err);
        this.currentReservation = { error: err.message };
      }
    },
    async fetchUpcomingReservations(spotId) {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/spots/${spotId}/upcoming-reservations`, {
          headers: { 'auth-token': token }
        });

        if (response.ok) {
          const data = await response.json();
          console.log('Upcoming reservations data:', data);
          this.upcomingReservations = Array.isArray(data) ? data : [];
        } else {
          const errorData = await response.json();
          console.error('Failed to fetch upcoming reservations:', errorData);
          this.upcomingReservations = [];
        }
      } catch (err) {
        console.error('Error fetching upcoming reservations:', err);
        this.upcomingReservations = [];
      }
    },
    async updateSpotStatus(newStatus) {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/parking_lots/${this.selectedLot.id}/spots/${this.selectedSpot.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          },
          body: JSON.stringify({ status: newStatus })
        });

        if (response.ok) {
          // Update the spot status locally
          this.selectedSpot.status = newStatus;

          // Emit event to refresh parking lots data
          this.$emit('refresh-lots');

          // Show success message
          alert(`Spot status updated to ${this.getStatusText(newStatus)}`);
        } else {
          const errorData = await response.json();
          alert(errorData.error || 'Failed to update spot status');
        }
      } catch (err) {
        console.error('Error updating spot status:', err);
        alert('Error updating spot status. Please try again.');
      }
    },
    async forceReleaseSpot() {
      if (!confirm('Are you sure you want to force release this spot? This will end the current reservation.')) {
        return;
      }

      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/spots/${this.selectedSpot.id}/force-release`, {
          method: 'POST',
          headers: { 'auth-token': token }
        });

        if (response.ok) {
          // Update the spot status locally
          this.selectedSpot.status = 'A';

          // Emit event to refresh parking lots data
          this.$emit('refresh-lots');

          // Close modal and show success message
          this.closeModal();
          alert('Spot has been successfully released');
        } else {
          const errorData = await response.json();
          alert(errorData.error || 'Failed to release spot');
        }
      } catch (err) {
        console.error('Error releasing spot:', err);
        alert('Error releasing spot. Please try again.');
      }
    },
    formatDateTime(dateTimeStr) {
      if (!dateTimeStr) return 'N/A';
      const date = new Date(dateTimeStr);
      
      // Format: "Nov 17, 2:30 PM" (no year, no seconds)
      const options = {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      };
      
      return date.toLocaleString('en-US', options);
    },
    calculateDuration(startTimeStr) {
      if (!startTimeStr) return 'N/A';

      const startTime = new Date(startTimeStr);
      const now = new Date();
      const diffMs = now - startTime;

      // Convert to hours and minutes
      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

      return `${hours}h ${minutes}m`;
    },
    async toggleLotStatus(lot) {
      const action = lot.isActive ? 'deactivate' : 'activate';
      
      if (!confirm(`Are you sure you want to ${action} "${lot.name}"?`)) {
        return;
      }

      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/parking_lots/${lot.id}/toggle`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          }
        });

        if (response.ok) {
          const result = await response.json();
          
          // Update the lot status locally
          lot.isActive = result.lot.is_active;
          
          // Emit event to refresh parking lots data
          this.$emit('refresh-lots');
          
          // Show success message
          alert(result.message);
        } else {
          const errorData = await response.json();
          alert(errorData.error || `Failed to ${action} parking lot`);
        }
      } catch (err) {
        console.error(`Error ${action}ing parking lot:`, err);
        alert(`Error ${action}ing parking lot. Please try again.`);
      }
    }
  }
};
</script>

<style scoped>
.parking-visualizer {
  width: 100%;
}

.status-legend {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-box {
  width: 15px;
  height: 15px;
  border-radius: 3px;
}

.status-box.available {
  background-color: #e0e0e0;
}

.status-box.booked {
  background-color: #4caf50;
}

.status-box.occupied {
  background-color: #f44336;
}

.status-box.unavailable {
  background-color: #616161;
}

.status-box.inactive-lot-legend {
  background-color: #757575;
  opacity: 0.7;
}

.parking-lots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.parking-lot-card {
  background-color: #2196f3;
  border-radius: 10px;
  padding: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
  height: 300px;
  /* Fixed height for all cards */
  display: flex;
  flex-direction: column;
}

.parking-lot-card.inactive-lot {
  background-color: #757575;
  opacity: 0.7;
}

.lot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  color: white;
}

.lot-header h3 {
  margin: 0;
  font-size: 0.9rem;
  flex-grow: 1;
}

.lot-status {
  font-size: 0.8rem;
  margin-right: 10px;
}

.menu-button {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0 5px;
}

.parking-slots {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(15px, 1fr));
  gap: 3.5px;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

/* Hide scrollbar for all browsers */
.parking-slots::-webkit-scrollbar {
  display: none;
  /* WebKit browsers (Chrome, Safari, Edge) */
}

.parking-slot {
  width: 15px;
  height: 15px;
  border-radius: 2px;
  cursor: pointer;
  transition: transform 0.2s;
}

.parking-slot:hover {
  transform: scale(1.1);
}

.parking-slot.available {
  background-color: #e0e0e0;
}

.parking-slot.booked {
  background-color: #4caf50;
}

.parking-slot.occupied {
  background-color: #f44336;
}

.parking-slot.unavailable {
  background-color: #616161;
}

/* Add Lot Card */
.add-lot-card {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.8), rgba(25, 118, 210, 0.9));
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  /* border: 2px dashed rgba(255, 255, 255, 0.5); */
}

.add-lot-card:hover {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.9), rgba(25, 118, 210, 1));
  border-color: rgba(255, 255, 255, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.add-lot-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: white;
  text-align: center;
}

.add-icon {
  font-size: 3rem;
  margin-bottom: 15px;
  opacity: 0.9;
}

.add-lot-content span {
  font-size: 1.1rem;
  font-weight: 500;
  opacity: 0.95;
}

/* Floating Add Button */
.floating-add-btn {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2196f3, #1976d2);
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(33, 150, 243, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.floating-add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(33, 150, 243, 0.6);
  background: linear-gradient(135deg, #1976d2, #1565c0);
}

.floating-add-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 15px rgba(33, 150, 243, 0.4);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background-color: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
}

.modal-content {
  padding: 20px;
}

.spot-info {
  margin-bottom: 20px;
}

.status-A {
  color: #2e7d32;
}

.status-B {
  color: #1565c0;
}

.status-O {
  color: #c62828;
}

.status-X {
  color: #616161;
}

.current-reservation,
.upcoming-reservations {
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #e1e4e8;
}

.current-reservation h4,
.upcoming-reservations h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #2c3e50;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-reservation h4 i,
.upcoming-reservations h4 i {
  color: #667eea;
}

.reservation-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  font-weight: 600;
  color: #6c757d;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-row .value {
  font-weight: 500;
  color: #2c3e50;
  font-size: 14px;
  text-align: right;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-active {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

.status-confirmed {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
}

.cost-value {
  color: #4caf50;
  font-weight: 700;
  font-size: 16px;
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.loading-state i {
  font-size: 2rem;
  color: #667eea;
  margin-bottom: 12px;
}

.error-state {
  text-align: center;
  padding: 40px 20px;
  background: #fff5f5;
  border-radius: 8px;
  border: 1px solid #feb2b2;
}

.error-state i {
  font-size: 2rem;
  color: #f56565;
  margin-bottom: 12px;
  display: block;
}

.error-state p {
  margin: 0;
  color: #c53030;
  font-size: 14px;
}

.no-data-message {
  text-align: center;
  padding: 20px;
  color: #718096;
}

.no-data-message p {
  margin: 8px 0;
  font-size: 14px;
}

.no-data-message .hint {
  font-size: 12px;
  color: #a0aec0;
  font-style: italic;
}

.spot-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.action-button {
  padding: 8px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.mark-unavailable {
  background-color: #616161;
  color: white;
}

.mark-available {
  background-color: #4caf50;
  color: white;
}

.force-release {
  background-color: #f44336;
  color: white;
}

/* Toggle Button Styles */
.toggle-button {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s ease;
  z-index: 10;
}

.toggle-button.active {
  color: #4caf50;
}

.toggle-button.active:hover {
  background-color: rgba(76, 175, 80, 0.1);
  color: #388e3c;
}

.toggle-button.inactive {
  color: #f44336;
}

.toggle-button.inactive:hover {
  background-color: rgba(244, 67, 54, 0.1);
  color: #d32f2f;
}

.toggle-button:active {
  transform: scale(0.95);
}
</style>