<template>
  <div v-if="reservation" class="space-y-4 p-4">
    <div class="lot-info text-sm text-gray-600">
      <p class="font-bold text-base text-gray-800">Booking ID: {{ formattedBookingId }}</p>
      <hr class="my-2">
      <p><span class="font-semibold">Parking Lot:</span> {{ reservation.parking_lot?.name || 'N/A' }}</p>
      <p><span class="font-semibold">Address:</span> {{ reservation.parking_lot?.address || 'N/A' }}</p>
      <p><span class="font-semibold">Spot:</span> {{ reservation.spot?.spot_number || 'Not Assigned' }}</p>
      <hr class="my-2">
      <p><span class="font-semibold">User:</span> {{ reservation.user ? `${reservation.user.first_name || ''} ${reservation.user.last_name || ''}`.trim() : 'N/A' }}</p>
      <p><span class="font-semibold">Vehicle:</span> {{ reservation.vehicle ? `${reservation.vehicle.model} (${reservation.vehicle.license_plate})` : 'N/A' }}</p>
      <hr class="my-2">
      <p><span class="font-semibold">Check-in:</span> {{ formatTime(reservation.parking_timestamp) }}</p>
      <p><span class="font-semibold">Check-out:</span> {{ formatTime(reservation.leaving_timestamp) }}</p>
      <p><span class="font-semibold">Duration:</span> {{ calculateDuration(reservation.parking_timestamp, reservation.leaving_timestamp) }}</p>
      <hr class="my-2">
      <p><span class="font-semibold">Status:</span> <span :class="statusClass(reservation.status)">{{ reservation.status }}</span></p>
      <p><span class="font-semibold">Cost:</span> ₹{{ reservation.parking_cost != null ? reservation.parking_cost.toFixed(2) : '0.00' }}</p>

    </div>
  </div>
  <div v-else class="p-4 text-center text-gray-500">
    <p>Loading reservation details...</p>
  </div>
</template>

<script>
export default {
  name: 'ReservationDetailModal',
  props: {
    reservation: {
      type: Object,
      default: null
    }
  },
  computed: {
    formattedBookingId() {
      if (!this.reservation || !this.reservation.booking_id) return 'N/A';
      return this.reservation.booking_id;
    }
  },
  methods: {
    formatTime(timestamp) {
      if (!timestamp) return 'N/A';
      return new Date(timestamp).toLocaleString();
    },
    calculateDuration(start, end) {
      if (!start || !end) return 'N/A';
      const startDate = new Date(start);
      const endDate = new Date(end);
      let diff = endDate.getTime() - startDate.getTime();

      const hours = Math.floor(diff / (1000 * 60 * 60));
      diff -= hours * (1000 * 60 * 60);

      const minutes = Math.floor(diff / (1000 * 60));

      return `${hours}h ${minutes}m`;
    },
    statusClass(status) {
      const classes = {
        'Booked': 'text-blue-600',
        'Confirmed': 'text-blue-600',
        'Active': 'text-green-600',
        'Completed': 'text-purple-600',
        'Cancelled': 'text-red-600',
        'Expired': 'text-gray-600'
      };
      return classes[status] || 'text-gray-800';
    }
  }
};
</script>

<style scoped>
.lot-info p {
  margin-bottom: 0.5rem;
}
</style>
