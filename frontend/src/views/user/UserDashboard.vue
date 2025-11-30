<template>
  <div class="user-dashboard">
    <!-- Toast Notifications -->
    <Toast ref="toast" />

    <!-- Sidebar -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2><i class="fas fa-parking"></i> ParkEase</h2>
        <p class="user-role">User Panel</p>
      </div>

      <nav class="sidebar-nav">
        <button @click="activeTab = 'home'" :class="{ 'active': activeTab === 'home' }" class="nav-item">
          <span class="nav-icon"><i class="fas fa-home"></i></span>
          <span class="nav-text">Home</span>
        </button>
        <button @click="activeTab = 'bookings'" :class="{ 'active': activeTab === 'bookings' }" class="nav-item">
          <span class="nav-icon"><i class="fas fa-ticket-alt"></i></span>
          <span class="nav-text">My Bookings</span>
        </button>
        <button @click="activeTab = 'lots'" :class="{ 'active': activeTab === 'lots' }" class="nav-item">
          <span class="nav-icon"><i class="fas fa-parking"></i></span>
          <span class="nav-text">Explore Lots</span>
        </button>
        <button @click="activeTab = 'profile'" :class="{ 'active': activeTab === 'profile' }" class="nav-item">
          <span class="nav-icon"><i class="fas fa-user"></i></span>
          <span class="nav-text">Profile</span>
        </button>
        <button @click="activeTab = 'analytics'" :class="{ 'active': activeTab === 'analytics' }" class="nav-item">
          <span class="nav-icon"><i class="fas fa-chart-line"></i></span>
          <span class="nav-text">My Analytics</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <button class="logout-btn" @click="logout">
          <span class="nav-icon"><i class="fas fa-sign-out-alt"></i></span>
          <span class="nav-text">Logout</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <div class="content-header">
        <div class="header-left">
          <h1>{{ getTabTitle() }}</h1>
          <p v-if="getWelcomeMessage()" class="welcome-message">{{ getWelcomeMessage() }}</p>
        </div>
        <div class="header-right">
          <div class="global-search-bar">
            <i class="fas fa-search"></i>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search parking lots..."
              @input="handleSearch"
            />
            <button v-if="searchQuery" @click="clearSearch" class="clear-search-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Profile Completion Banner -->
      <div v-if="profileLoaded && profile && ((profile.profile_completion < 100 || !profile.can_book) && showProfileBanner)"
        class="profile-completion-banner">
        <div class="banner-content">
          <div class="banner-left">
            <h3><i class="fas fa-info-circle"></i> Complete Your Profile</h3>
            <p class="banner-subtitle">{{ (profile && profile.profile_completion) || 0 }}% Complete - Missing: {{ (profile && profile.missing_fields || []).join(', ') }}</p>
          </div>
          <div class="banner-actions">
            <button @click="completeProfileClick" class="complete-profile-btn">
              Complete Now
            </button>
            <button @click="showProfileBanner = false" class="dismiss-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- User Overview Cards - Visible on analytics tab only -->
      <div v-if="activeTab === 'analytics'" class="analytics-overview">
        <div class="stat-card">
          <h3>{{ (userAnalytics && userAnalytics.overview && userAnalytics.overview.total_reservations) || 0 }}</h3>
          <p>Total Bookings</p>
        </div>
        <div class="stat-card">
          <h3>₹{{ formatInteger((userAnalytics && userAnalytics.overview && userAnalytics.overview.total_spent) || 0) }}</h3>
          <p>Total Spent</p>
        </div>
        <div class="stat-card">
          <h3>{{ (userAnalytics && userAnalytics.overview && userAnalytics.overview.completion_rate) || 0 }}%</h3>
          <p>Completion Rate</p>
        </div>
        <div class="stat-card">
          <h3>{{ (vehicleCrud && vehicleCrud.items && vehicleCrud.items.value && vehicleCrud.items.value.length) || 0 }}
          </h3>
          <p>My Vehicles</p>
        </div>
      </div>

      <!-- Home Tab -->
      <div v-if="activeTab === 'home'" class="tab-content">
        <!-- Home Dashboard Grid -->
        <div class="home-dashboard-grid">
          <!-- Currently Parked Vehicle (Top Left) -->
          <div class="dashboard-card currently-parked">
            <div class="card-header">
              <h3><i class="fas fa-car"></i> Currently Parked</h3>
            </div>
            <div class="card-content">
              <div v-if="currentlyParked" class="parked-info-clean">
                <div class="parked-main">
                  <div class="parked-left">
                    <div class="vehicle-badge">
                      <i class="fas fa-car"></i>
                      <span>{{ currentlyParked.vehicle_number }} at {{ currentlyParked.spot_number }}</span>
                    </div>
                    <div class="parked-meta">
                      <div class="meta-row">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>{{ currentlyParked.lot_name }}</span>
                      </div>
                      <div class="meta-row">
                        <i class="fas fa-clock"></i>
                        <span>Since {{ formatTimeOnly(currentlyParked.parking_timestamp) }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="parked-right">
                    <div class="time-info">
                      <div class="duration-badge duration-live">
                        <i class="fas fa-clock"></i>
                        {{ liveParkingDuration }}
                      </div>
                    </div>
                    <button @click="parkOut(currentlyParked.id)" class="park-out-btn-clean">
                      <i class="fas fa-sign-out-alt"></i> Park Out
                    </button>
                  </div>
                </div>
              </div>
              <div v-else class="no-data">
                <i class="fas fa-car-side"></i>
                <p>No vehicle currently parked</p>
              </div>
            </div>
          </div>

          <!-- Explore Lots (Top Right) -->
          <div class="dashboard-card explore-lots">
            <div class="card-header">
              <h3><i class="fas fa-map-marker-alt"></i> Explore Lots</h3>
              <button v-if="featuredLots.length > 0" @click="activeTab = 'lots'" class="view-all-btn-header">
                <i class="fas fa-eye"></i> View All
              </button>
            </div>
            <div class="card-content">
              <div v-if="featuredLots.length > 0" class="lots-grid">
                <div v-for="lot in featuredLots" :key="lot.id" class="lot-card" @click="showLotDetails(lot)">
                  <h4>{{ lot.location }}</h4>
                  <p><i class="fas fa-parking"></i> {{ lot.availableSpots }} spots</p>
                  <p><i class="fas fa-rupee-sign"></i> ₹{{ formatInteger(lot.price) }}/hr</p>
                </div>
              </div>
              <div v-else class="no-data">
                <i class="fas fa-parking"></i>
                <p>No parking lots available</p>
              </div>
            </div>
          </div>

          <!-- Upcoming Booking (Bottom Left) -->
          <div class="dashboard-card upcoming-booking">
            <div class="card-header">
              <h3><i class="fas fa-clock"></i> Upcoming Booking</h3>
              <button v-if="upcomingBooking && upcomingBooking.status === 'Confirmed'" @click="parkIn(upcomingBooking.id)" class="park-in-btn-header">
                <i class="fas fa-sign-in-alt"></i> Park In
              </button>
            </div>
            <div class="card-content">
              <div v-if="upcomingBooking" class="booking-info-sober">
                <div class="booking-row">
                  <span class="booking-label">Booking ID:</span>
                  <a href="#" @click.prevent="showBookingDetails(upcomingBooking)" class="booking-id-link-sober">
                    {{ upcomingBooking.bookingId }}
                  </a>
                </div>
                
                <div class="booking-row">
                  <span class="booking-label">Location:</span>
                  <span class="booking-value">{{ upcomingBooking.lot_name }}</span>
                </div>
                
                <div class="booking-row">
                  <span class="booking-label">Arrival:</span>
                  <span class="booking-value">{{ formatTime(upcomingBooking.expected_arrival) }}</span>
                </div>
                
                <div class="booking-row">
                  <span class="booking-label">Departure:</span>
                  <span class="booking-value">{{ formatTime(upcomingBooking.expected_departure) }}</span>
                </div>
              </div>
              <div v-else class="no-data">
                <i class="fas fa-calendar-alt"></i>
                <p>No upcoming bookings</p>
              </div>
            </div>
          </div>

          <!-- Parking History (Bottom Right) -->
          <div class="dashboard-card parking-history">
            <div class="card-header">
              <h3><i class="fas fa-history"></i> Recent History</h3>
              <button v-if="recentHistory.length > 0" @click="activeTab = 'profile'" class="view-all-btn-header">
                <i class="fas fa-list"></i> View All
              </button>
            </div>
            <div class="card-content">
              <div v-if="recentHistory.length > 0" class="history-table-compact">
                <table class="compact-history-table">
                  <thead>
                    <tr>
                      <th>Booking ID</th>
                      <th>Location</th>
                      <th>Date</th>
                      <th>Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="history in recentHistory.slice(0, 5)" :key="history.id">
                      <td>
                        <a href="#" @click.prevent="showHistoryDetails(history)" class="booking-id-link">
                          {{ history.bookingId || 'BOOK-' + history.id }}
                        </a>
                      </td>
                      <td>{{ history.lot_name }}</td>
                      <td>{{ formatDate(history.parking_timestamp) }}</td>
                      <td>₹{{ formatInteger(history.parking_cost) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="no-data">
                <i class="fas fa-history"></i>
                <p>No parking history</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Floating Book Parking Button for Home Tab -->
        <button @click="openBookingModal" class="floating-book-btn floating-book-btn-small">
          <i class="fas fa-plus"></i>
          Book Parking
        </button>
      </div>

      <!-- Bookings Tab -->
      <div v-if="activeTab === 'bookings'" class="tab-content bookings-tab-content">
        <!-- Bookings Grid Layout -->
        <div class="bookings-grid">
          <!-- Top Left: Confirmed Bookings -->
          <div class="booking-table-card">
            <div class="table-card-header">
              <h3><i class="fas fa-clock"></i> Confirmed Bookings | {{ upcomingBookings.length }}</h3>
            </div>
            <div class="table-card-content">
              <DataTable :items="upcomingBookings" :columns="confirmedBookingColumns" :show-actions="false"
                empty-message="No confirmed bookings" :show-pagination="false" :always-show-headers="true">
                <template #cell-bookingId="{ value, item }">
                  <a href="#" @click.prevent="showBookingDetails(item)" class="booking-id-link">
                    {{ value }}
                  </a>
                </template>
              </DataTable>
            </div>
          </div>

          <!-- Top Right: Pending Requests -->
          <div class="booking-table-card">
            <div class="table-card-header">
              <h3><i class="fas fa-hourglass-half"></i> Pending Requests | {{ pendingBookings.length }}</h3>
            </div>
            <div class="table-card-content">
              <DataTable :items="pendingBookings" :columns="pendingBookingColumns" :show-actions="false"
                empty-message="No pending requests" :show-pagination="false" :always-show-headers="true">
                <template #cell-bookingId="{ value, item }">
                  <a href="#" @click.prevent="showBookingDetails(item)" class="booking-id-link">
                    {{ value }}
                  </a>
                </template>
              </DataTable>
            </div>
          </div>

          <!-- Bottom Left: Cancelled/Rejected Bookings -->
          <div class="booking-table-card">
            <div class="table-card-header">
              <h3><i class="fas fa-times-circle"></i> Cancelled/Rejected Bookings | {{ cancelledBookings.length }}</h3>
            </div>
            <div class="table-card-content">
              <DataTable :items="cancelledBookings" :columns="cancelledBookingColumns" :show-actions="false"
                empty-message="No cancelled/rejected bookings" :show-pagination="false" :always-show-headers="true">
                <template #cell-bookingId="{ value, item }">
                  <a href="#" @click.prevent="showBookingDetails(item)" class="booking-id-link">
                    {{ value }}
                  </a>
                </template>
                <template #cell-status="{ value }">
                  <span class="status-cancelled">{{ value }}</span>
                </template>
              </DataTable>
            </div>
          </div>

          <!-- Bottom Right: Parking History -->
          <div class="booking-table-card">
            <div class="table-card-header">
              <h3><i class="fas fa-history"></i> Parking History | {{ historyBookings.length }}</h3>
            </div>
            <div class="table-card-content">
              <DataTable :items="historyBookings" :columns="historyBookingColumns" :show-actions="false"
                empty-message="No parking history" :show-pagination="false" :always-show-headers="true">
                <template #cell-bookingId="{ value, item }">
                  <a href="#" @click.prevent="showBookingDetails(item)" class="booking-id-link">
                    {{ value }}
                  </a>
                </template>
                <template #cell-rating="{ value }">
                  <span class="rating-stars">{{ value }}</span>
                </template>
              </DataTable>
            </div>
          </div>
        </div>

        <!-- Floating Book Parking Button -->
        <button @click="openBookingModal" class="floating-book-btn floating-book-btn-small">
          <i class="fas fa-plus"></i>
          Book Parking
        </button>
      </div>

      <!-- Available Lots Tab -->
      <div v-if="activeTab === 'lots'" class="tab-content">
        <div class="lots-container">
          <div v-for="lot in lots" :key="lot.id" class="parking-lot-card">
            <div class="lot-header">
              <div class="lot-title">
                <h3 @click="showLotDetails(lot)" class="clickable-title">{{ lot.name }}</h3>
                <div class="availability-indicator" :class="{ 'active': lot.isActive, 'inactive': !lot.isActive }">
                </div>
              </div>
            </div>

            <div class="lot-info-row">
              <div class="info-item">
                <i class="fas fa-rupee-sign"></i>
                <span class="info-label">Price/hr:</span>
                <span class="info-value">₹{{ formatInteger(lot.price) || '10' }}</span>
              </div>

              <div class="info-item">
                <i class="fas fa-car"></i>
                <span class="info-label">Available Spots:</span>
                <span class="info-value">{{ lot.availableSpots }}/{{ lot.capacity }}</span>
              </div>

              <div class="info-item">
                <i class="fas fa-clock"></i>
                <span class="info-label">Time:</span>
                <span class="info-value">{{ getDisplayHours(lot) }}</span>
              </div>
            </div>

            <div class="lot-actions">
              <button @click="showLotDetails(lot)" class="action-btn details-btn">
                <i class="fas fa-info-circle"></i>
                Details
              </button>
              <button @click="openBookModalForLot(lot)" class="action-btn book-btn"
                :disabled="!lot.isActive || lot.availableSpots === 0">
                <i class="fas fa-ticket-alt"></i>
                Book
              </button>
              <button @click="toggleFavorite(lot)" class="action-btn save-btn" :class="{ 'favorited': lot.isFavorite }" :title="lot.isFavorite ? 'Remove from favorites' : 'Add to favorites'">
                <i :class="lot.isFavorite ? 'fas fa-heart' : 'far fa-heart'"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="lots.length === 0" class="no-lots-available">
          <i class="fas fa-parking"></i>
          <h3>No Parking Lots Available</h3>
          <p>There are currently no parking lots available. Please check back later.</p>
        </div>
      </div>

      <!-- Profile Tab -->
      <div v-if="activeTab === 'profile'" class="tab-content">
        
        <!-- Profile Card with Avatar -->
        <div class="profile-card-modern">
          <div class="profile-left">
            <div class="profile-avatar">
              <i class="fas fa-user"></i>
            </div>
            <div class="profile-info-main">
              <h2>{{ profile.first_name }} {{ profile.last_name }} 
                <button @click="openProfileEditModal" class="edit-icon-btn">
                  <i class="fas fa-edit"></i>
                </button>
              </h2>
              <div class="profile-detail-row">
                <i class="fas fa-user"></i>
                <span>@{{ profile.username }}</span>
              </div>
              <div class="profile-detail-row">
                <i class="fas fa-envelope"></i>
                <span>{{ profile.email }}</span>
              </div>
              <div class="profile-detail-row">
                <i class="fas fa-phone"></i>
                <span>{{ profile.phone_number || 'Not provided' }}</span>
              </div>
              <div class="profile-detail-row">
                <i class="fas fa-map-marker-alt"></i>
                <span>{{ profile.address || 'Not provided' }}</span>
              </div>
              <div class="profile-status-badge">
                <span class="status-active">Active</span>
              </div>
            </div>
          </div>
          
          <div class="profile-right">
            <div class="profile-stat-card">
              <div class="stat-label">Total Bookings</div>
              <div class="stat-value-large">{{ userAnalytics.overview?.total_reservations || 0 }}</div>
            </div>
            <div class="profile-stat-card">
              <div class="stat-label">Total Spent</div>
              <div class="stat-value-large">₹{{ formatInteger(userAnalytics.overview?.total_spent || 0) }}</div>
            </div>
            <div class="profile-stat-card">
              <div class="stat-label">Avg. Rating Given</div>
              <div class="stat-value-large">{{ userAnalytics.overview?.avg_rating_given || 0 }} <i class="fas fa-star" style="color: #ffc107; font-size: 16px;"></i></div>
            </div>
            <div class="profile-stat-card">
              <div class="stat-label">Member Since</div>
              <div class="stat-value-large">{{ formatDate(profile.created_at).split(',')[0] }}</div>
            </div>
          </div>
        </div>

        <!-- Vehicles and Favorites Side by Side -->
        <div class="profile-grid-2col">
          <!-- My Vehicles Section -->
          <div class="profile-section">
            <div class="section-header-with-controls">
              <h3>My Vehicles</h3>
              <button @click="vehicleCrud.openAddModal()" class="add-vehicle-btn-header">
                <i class="fas fa-plus"></i> Add Vehicle
              </button>
            </div>
            <div class="vehicles-section">
              <div v-if="vehicleCrud.items.value && vehicleCrud.items.value.length > 0" class="vehicles-grid">
                <div v-for="vehicle in vehicleCrud.items.value" :key="vehicle.id" class="vehicle-card">
                  <div class="vehicle-icon">
                    <i class="fas fa-car"></i>
                  </div>
                  <div class="vehicle-info">
                    <div class="vehicle-number">{{ vehicle.vehicle_number }}</div>
                    <div class="vehicle-details">
                      <span class="vehicle-type">{{ vehicle.vehicle_name }}</span>
                      <span v-if="vehicle.color" class="vehicle-color">
                        <i class="fas fa-circle" :style="{ color: vehicle.color }"></i>
                        {{ vehicle.color }}
                      </span>
                    </div>
                  </div>
                  <div class="vehicle-actions">
                    <button @click="vehicleCrud.editItem(vehicle)" class="vehicle-action-btn edit-btn" title="Edit">
                      <i class="fas fa-edit"></i>
                    </button>
                    <button @click="vehicleCrud.deleteItem(vehicle.id)" class="vehicle-action-btn delete-btn" title="Delete">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
              <div v-else class="no-vehicles">
                <i class="fas fa-car"></i>
                <p>No vehicles added yet</p>
                <small>Add your first vehicle to start booking parking spots</small>
              </div>
            </div>
          </div>

          <!-- Favorite Parking Lots Section -->
          <div class="profile-section">
            <h3>Favorite Parking Lots</h3>
            <div class="favorites-section">
              <div v-if="favoriteLots.length > 0" class="favorites-grid">
                <div v-for="lot in favoriteLots" :key="lot.id" class="favorite-lot-card">
                  <div class="favorite-lot-header">
                    <h4>{{ lot.name }}</h4>
                    <button @click="toggleFavorite(lot)" class="remove-favorite-btn" title="Remove from favorites">
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                  <div class="favorite-lot-details">
                    <div class="favorite-detail">
                      <i class="fas fa-map-marker-alt"></i>
                      <span>{{ lot.location }}</span>
                    </div>
                    <div class="favorite-detail">
                      <i class="fas fa-rupee-sign"></i>
                      <span>₹{{ formatInteger(lot.price) || '10' }}/hour</span>
                    </div>
                    <div class="favorite-detail">
                      <i class="fas fa-car"></i>
                      <span>{{ lot.availableSpots }}/{{ lot.capacity }} spots</span>
                    </div>
                  </div>
                  <div class="favorite-lot-actions">
                    <button @click="openBookModalForLot(lot)" class="quick-book-btn" :disabled="lot.availableSpots === 0">
                      <i class="fas fa-ticket-alt"></i>
                      Quick Book
                    </button>
                  </div>
                </div>
              </div>
              <div v-else class="no-favorites">
                <i class="fas fa-heart"></i>
                <p>No favorite parking lots yet</p>
                <small>Save parking lots from the Available Lots tab to see them here</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Parking History Section -->
        <div class="profile-section">
          <div class="section-header-with-controls">
            <h3>Parking History</h3>
            <div class="sort-control">
              <label>Sort by:</label>
              <select v-model="historySortBy" class="sort-select">
                <option value="date">Date</option>
                <option value="cost">Cost</option>
                <option value="duration">Duration</option>
              </select>
            </div>
          </div>
          <div class="history-table-section">
            <DataTable 
              :items="paginatedHistory" 
              :columns="profileHistoryColumns" 
              :show-actions="false"
              empty-message="No parking history found."
              :show-pagination="true"
              :current-page="historyPage"
              :total-pages="totalHistoryPages"
              @page-change="historyPage = $event"
            >
              <template #cell-bookingId="{ value, item }">
                <a href="#" @click.prevent="showBookingDetails(item)" class="booking-id-link">
                  {{ value }}
                </a>
              </template>
              <template #cell-status="{ value }">
                <span class="status-badge" :class="`status-${value.toLowerCase().replace(/\s+/g, '-')}`">
                  {{ value }}
                </span>
              </template>
              <template #cell-rating="{ value }">
                <span class="rating-stars">{{ value || 'Not rated' }}</span>
              </template>
            </DataTable>
          </div>
        </div>

        <!-- Danger Zone -->
        <div class="profile-section danger-zone">
          <h3>⚠️ Danger Zone</h3>
          <p>Once you delete your account, there is no going back. Please be certain.</p>
          <button @click="showDeleteAccountModal = true" class="delete-account-btn">
            Delete My Account
          </button>
        </div>
      </div>



      <!-- Analytics Tab -->
      <div v-if="activeTab === 'analytics'" class="tab-content">
        <!-- Analytics Grid -->
        <div class="analytics-grid">
          <!-- Top Parking Locations -->
          <div class="analytics-card">
            <div class="analytics-card-header">
              <h3><i class="fas fa-map-marker-alt"></i> Top Parking Locations</h3>
            </div>
            <div class="analytics-card-content">
              <div v-if="topLocations.length > 0" class="top-locations-list">
                <div v-for="(location, index) in topLocations" :key="index" class="location-item">
                  <div class="location-rank">{{ index + 1 }}</div>
                  <div class="location-info">
                    <div class="location-name">{{ location.name }}</div>
                    <div class="location-stats">{{ location.visits }} visits • ₹{{ formatInteger(location.spent) }}</div>
                  </div>
                  <div class="location-bar">
                    <div class="location-bar-fill" :style="{ width: (location.visits / topLocations[0].visits * 100) + '%' }"></div>
                  </div>
                </div>
              </div>
              <div v-else class="no-analytics-data">
                <i class="fas fa-chart-bar"></i>
                <p>No data available yet</p>
              </div>
            </div>
          </div>

          <!-- Parking Patterns -->
          <div class="analytics-card">
            <div class="analytics-card-header">
              <h3><i class="fas fa-clock"></i> Parking Patterns</h3>
            </div>
            <div class="analytics-card-content">
              <div class="pattern-stats">
                <div class="pattern-item">
                  <div class="pattern-label">Average Duration</div>
                  <div class="pattern-value">{{ averageDuration }}</div>
                </div>
                <div class="pattern-item">
                  <div class="pattern-label">Most Common Day</div>
                  <div class="pattern-value">{{ mostCommonDay }}</div>
                </div>
                <div class="pattern-item">
                  <div class="pattern-label">Preferred Time</div>
                  <div class="pattern-value">{{ preferredTime }}</div>
                </div>
                <div class="pattern-item">
                  <div class="pattern-label">Avg. Cost/Visit</div>
                  <div class="pattern-value">₹{{ averageCostPerVisit }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Monthly Spending Chart -->
          <div class="analytics-card chart-card">
            <div class="analytics-card-header">
              <h3><i class="fas fa-chart-line"></i> Monthly Spending Trend</h3>
            </div>
            <div class="analytics-card-content">
              <Chart v-if="spendingChartData.data.length > 0" type="line" title="" :data="spendingChartData.data"
                :labels="spendingChartData.labels" color="#667eea" data-label="Spending (₹)" 
                x-axis-label="Month" y-axis-label="Amount (₹)" />
              <div v-else class="no-analytics-data">
                <i class="fas fa-chart-line"></i>
                <p>No spending data yet</p>
              </div>
            </div>
          </div>

          <!-- Weekly Activity Chart -->
          <div class="analytics-card chart-card">
            <div class="analytics-card-header">
              <h3><i class="fas fa-chart-bar"></i> Weekly Activity</h3>
            </div>
            <div class="analytics-card-content">
              <Chart v-if="weeklyChartData.data.length > 0" type="bar" title="" :data="weeklyChartData.data"
                :labels="weeklyChartData.labels" color="#28a745" data-label="Bookings" 
                x-axis-label="Date" y-axis-label="Number of Bookings" />
              <div v-else class="no-analytics-data">
                <i class="fas fa-chart-bar"></i>
                <p>No activity data yet</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Export Section -->
        <div class="export-section">
          <div class="export-header">
            <div class="export-title-group">
              <p class="export-kicker">Own your parking history</p>
              <h3><i class="fas fa-download"></i> Export Your Data</h3>
              <p class="export-subtitle">Get a CSV copy of every reservation, vehicle and billing detail in seconds.</p>
            </div>
            <div class="export-illustration">
              <i class="fas fa-file-alt"></i>
            </div>
          </div>

          <div class="export-actions">
            <button @click="exportCSV" :disabled="taskLoading" class="export-btn">
              <i class="fas fa-file-csv"></i>
              {{ taskLoading ? 'Generating...' : 'Export CSV Report' }}
            </button>
            <div class="export-hint">
              <i :class="taskLoading ? 'fas fa-spinner fa-spin' : 'fas fa-info-circle'"></i>
              <span>
                {{ taskLoading
                  ? 'We are generating your CSV. Hang tight…'
                  : 'You will receive an email with the download link when your CSV is ready.' }}
              </span>
            </div>
          </div>

          <!-- Export Status Message -->
          <div v-if="taskError" class="export-alert error">
            <i class="fas fa-exclamation-circle"></i>
            <div>
              <strong>Export failed</strong>
              <p>{{ taskError }}</p>
            </div>
          </div>

          <div v-if="taskResult && !taskError" :class="['export-alert', taskResult.email_sent ? 'success' : 'warning']">
            <i :class="taskResult.email_sent ? 'fas fa-check-circle' : 'fas fa-envelope-open-text'"></i>
            <div>
              <strong>{{ taskResult.email_sent ? 'Email sent' : 'CSV ready - email could not be delivered' }}</strong>
              <p>{{ taskResult.message }}</p>
              <small v-if="taskResult.user_email">Sent to: {{ taskResult.user_email }}</small>
              <small v-if="taskResult.email_message && !taskResult.email_sent">{{ taskResult.email_message }}</small>
            </div>
          </div>

          <div v-if="taskResult && taskResult.download_url" class="csv-download-ready">
            <div class="download-copy">
              <i class="fas fa-link"></i>
              <div>
                <p class="download-title">Direct download</p>
                <p class="download-subtext">Click below to grab <strong>{{ taskResult.filename }}</strong></p>
              </div>
            </div>
            <a :href="taskResult.download_url" class="download-link" download>
              <i class="fas fa-arrow-circle-down"></i>
              Download CSV
            </a>
          </div>
        </div>
      </div>

      <!-- Booking Modal -->
      <Modal :show="showAddBookingModal || showEditBookingModal"
        :title="(showEditBookingModal ? 'Edit' : 'Book') + ' Parking'"
        :submit-text="showEditBookingModal ? 'Update' : 'Book'" @close="closeBookingModal"
        @submit="showEditBookingModal ? updateBooking() : addBooking()" hide-actions>
        <form @submit.prevent="showEditBookingModal ? updateBooking() : addBooking()" class="booking-modal-form">
          <label>
            Lot:
            <select v-model="bookingForm.lotId" @change="fetchBookingData" required>
              <option value="">Select a parking lot</option>
              <option v-for="lot in lots" :value="lot.id" :key="lot.id">{{ lot.name }}</option>
            </select>
          </label>

          <div v-if="bookingForm.lotId && bookingData.lot.id" class="lot-info">
            <p><strong>Available Spots:</strong> {{ bookingData.lot.available_spots }}</p>
            <p><strong>Price:</strong> ₹{{ formatInteger(bookingData.lot.price) }}/hour</p>
            <p><strong>Operating Hours:</strong> {{ bookingData.lot.available_from }} - {{ bookingData.lot.available_to
            }}</p>
            <small class="operating-hours-note">Please select times within operating hours</small>
          </div>

          <div v-if="!bookingData.has_vehicles && bookingForm.lotId" class="error">
            <p>Please add a vehicle before booking.</p>
            <button type="button" @click="redirectToVehicles" class="redirect-btn">Add Vehicle Now</button>
          </div>

          <label v-if="bookingData.has_vehicles">
            Select Vehicle:
            <select v-model="bookingForm.vehicle_id" required>
              <option value="">Choose a vehicle</option>
              <option v-for="vehicle in bookingData.vehicles" :value="vehicle.id" :key="vehicle.id">
                {{ vehicle.vehicle_number }} ({{ vehicle.vehicle_name }})
              </option>
            </select>
          </label>

          <div class="time-fields" v-if="bookingData.has_vehicles">
            <label>
              Arrival: <span class="required">*</span>
              <input v-model="bookingForm.expected_arrival" type="time" required placeholder="HH:MM" />
              <small>When do you plan to arrive?</small>
            </label>

            <label>
              Departure: <span class="required">*</span>
              <input v-model="bookingForm.expected_departure" type="time" required placeholder="HH:MM" />
              <small>When do you plan to leave?</small>
            </label>
          </div>

          <div v-if="bookingData.has_active_reservation" class="error">
            <p>You already have an active reservation. Please release it first.</p>
          </div>

          <div class="modal-actions">
            <button type="submit">{{ showEditBookingModal ? 'Update' : 'Book' }}</button>
            <button type="button" @click="closeBookingModal">Cancel</button>
          </div>
        </form>
      </Modal>

      <!-- Vehicle Modal -->
      <Modal :show="vehicleCrud.showAddModal.value || vehicleCrud.showEditModal.value"
        :title="(vehicleCrud.showEditModal.value ? 'Edit' : 'Add') + ' Vehicle'"
        :submit-text="vehicleCrud.showEditModal.value ? 'Update' : 'Add'" @close="vehicleCrud.closeModal"
        @submit="vehicleCrud.submitForm" hide-actions>
        <form @submit.prevent="vehicleCrud.submitForm">
          <label>
            Vehicle Number:
            <input v-model="vehicleCrud.form.vehicle_number" required />
          </label>
          <label>
            Vehicle Name:
            <input v-model="vehicleCrud.form.vehicle_name" required />
          </label>
          <label>
            Color:
            <input v-model="vehicleCrud.form.color" />
          </label>

          <div v-if="vehicleCrud.error.value" class="error-message">{{ vehicleCrud.error.value }}</div>
          <div v-if="vehicleCrud.success.value" class="success-message">{{ vehicleCrud.success.value }}</div>

          <div class="modal-actions">
            <button type="submit" :disabled="vehicleCrud.loading.value">
              {{ vehicleCrud.loading.value ? 'Processing...' : (vehicleCrud.showEditModal.value ? 'Update' : 'Add') }}
            </button>
            <button type="button" @click="vehicleCrud.closeModal" :disabled="vehicleCrud.loading.value">Cancel</button>
          </div>
        </form>
      </Modal>

      <!-- Delete Account Modal -->
      <Modal :show="showDeleteAccountModal" title="⚠️ Delete Account"
        :submit-text="deleting ? 'Deleting Account...' : 'Delete My Account Forever'"
        :submit-disabled="deleteForm.confirmation !== 'DELETE' || !deleteForm.password || deleting"
        submit-button-class="delete-confirm-btn" modal-class="delete-modal" @close="closeDeleteModal"
        @submit="deleteAccount" hide-actions>
        <div class="delete-warning">
          <p><strong>This action cannot be undone!</strong></p>
          <p>Deleting your account will permanently remove:</p>
          <ul>
            <li>Your profile and personal information</li>
            <li>All booking history and reservations</li>
            <li>All registered vehicles</li>
            <li>All payment records</li>
          </ul>
          <p>You will not be able to recover this data.</p>
        </div>

        <form @submit.prevent="deleteAccount">
          <label>
            Enter your password to confirm:
            <input v-model="deleteForm.password" type="password" required placeholder="Your current password" />
          </label>

          <label>
            Type "DELETE" to confirm:
            <input v-model="deleteForm.confirmation" type="text" required
              placeholder="Type DELETE in capital letters" />
          </label>

          <div v-if="deleteError" class="error-message">{{ deleteError }}</div>

          <div class="modal-actions">
            <button type="submit" class="delete-confirm-btn"
              :disabled="deleteForm.confirmation !== 'DELETE' || !deleteForm.password || deleting">
              {{ deleting ? 'Deleting Account...' : 'Delete My Account Forever' }}
            </button>
            <button type="button" @click="closeDeleteModal" :disabled="deleting">
              Cancel
            </button>
          </div>
        </form>
      </Modal>

      <!-- Lot Details Modal -->
      <Modal :show="showLotDetailsModal" title="Parking Lot Details" @close="closeLotDetailsModal" hide-actions>
        <div v-if="selectedLot" class="lot-details-modal">
          <div class="lot-header-section">
            <div class="lot-title-row">
              <h2 class="lot-modal-title">{{ selectedLot.name }}</h2>
              <div class="status-badge" :class="{ 'active': selectedLot.isActive, 'inactive': !selectedLot.isActive }">
                <div class="status-dot"></div>
                <span>{{ selectedLot.isActive ? 'Active' : 'Inactive' }}</span>
              </div>
            </div>
            <p class="lot-location">
              <i class="fas fa-map-marker-alt"></i>
              {{ selectedLot.location }}
            </p>
          </div>

          <div class="lot-info-sections">
            <div class="info-row">
              <div class="info-card">
                <div class="info-icon">
                  <i class="fas fa-rupee-sign"></i>
                </div>
                <div class="info-content">
                  <h4>Price per Hour</h4>
                  <p>₹{{ formatInteger(selectedLot.price) || '10' }}</p>
                </div>
              </div>

              <div class="info-card">
                <div class="info-icon">
                  <i class="fas fa-clock"></i>
                </div>
                <div class="info-content">
                  <h4>Operating Hours</h4>
                  <p>{{ getDisplayHours(selectedLot) }}</p>
                </div>
              </div>
            </div>

            <div class="capacity-section">
              <h4><i class="fas fa-car"></i> Parking Availability</h4>
              <div class="capacity-info">
                <div class="capacity-numbers">
                  <span class="available">{{ selectedLot.availableSpots }} Available</span>
                  <span class="total">{{ selectedLot.capacity }} Total</span>
                </div>
                <div class="capacity-bar">
                  <div class="capacity-fill"
                    :style="{ width: ((selectedLot.capacity - selectedLot.availableSpots) / selectedLot.capacity * 100) + '%' }">
                  </div>
                </div>
                <small class="occupancy-text">{{ Math.round((selectedLot.capacity - selectedLot.availableSpots) /
                  selectedLot.capacity * 100) }}% occupied</small>
              </div>
            </div>

            <div class="features-section">
              <h4><i class="fas fa-star"></i> Amenities & Features</h4>
              <div class="features-grid">
                <div class="feature-item">
                  <i class="fas fa-shield-alt"></i>
                  <span>24/7 Security</span>
                </div>
                <div class="feature-item">
                  <i class="fas fa-video"></i>
                  <span>CCTV Monitoring</span>
                </div>
                <div class="feature-item">
                  <i class="fas fa-wheelchair"></i>
                  <span>Accessible</span>
                </div>
                <div class="feature-item">
                  <i class="fas fa-car-side"></i>
                  <span>Covered Parking</span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <button v-if="selectedLot.isActive && selectedLot.availableSpots > 0" @click="bookFromDetails"
              class="book-from-details-btn">
              <i class="fas fa-ticket-alt"></i>
              Book This Lot
            </button>
            <button @click="toggleFavoriteFromDetails" class="favorite-from-details-btn"
              :class="{ 'favorited': selectedLot.isFavorite }" :title="selectedLot.isFavorite ? 'Remove from favorites' : 'Add to favorites'">
              <i :class="selectedLot.isFavorite ? 'fas fa-heart' : 'far fa-heart'"></i>
            </button>
            <button @click="closeLotDetailsModal" class="close-details-btn">
              Close
            </button>
          </div>
        </div>
      </Modal>

      <!-- Profile Edit Modal -->
      <Modal :show="showProfileEditModal" title="Edit Profile" @close="closeProfileEditModal" hide-actions>
        <form class="profile-edit-form" @submit.prevent="updateProfile">
          <div class="form-row">
            <label>
              First Name: <span class="required">*</span>
              <input v-model="profile.first_name" type="text" required />
            </label>
            <label>
              Last Name: <span class="required">*</span>
              <input v-model="profile.last_name" type="text" required />
            </label>
          </div>

          <label>
            Email:
            <input v-model="profile.email" type="email" disabled />
            <small>Email cannot be changed</small>
          </label>

          <label>
            Username:
            <input v-model="profile.username" type="text" required />
            <small>Auto-generated from your email, but you can change it</small>
          </label>

          <label>
            Phone Number: <span class="required">*</span>
            <input v-model="profile.phone_number" type="tel" maxlength="10" placeholder="Enter your phone number" />
            <small>Required for booking parking spots</small>
          </label>

          <label>
            Address:
            <textarea v-model="profile.address" rows="3" placeholder="Enter your full address"></textarea>
          </label>

          <label>
            PIN Code:
            <input v-model="profile.pincode" type="text" maxlength="6" placeholder="6-digit PIN code" />
          </label>

          <div class="form-divider"></div>

          <h4><i class="fas fa-bell"></i> Notification Preferences</h4>
          <p class="section-description">Choose how you want to receive parking reminders and updates</p>

          <label>
            <div class="notification-option">
              <div class="option-header">
                <i class="fas fa-envelope"></i>
                <span class="option-title">Email Notifications</span>
                <span class="badge-enabled">Always Enabled</span>
              </div>
              <small>You'll receive important updates via email at {{ profile.email }}</small>
            </div>
          </label>

          <label>
            <div class="notification-option">
              <div class="option-header">
                <i class="fab fa-google"></i>
                <span class="option-title">Google Chat Webhook (Optional)</span>
              </div>
              <input 
                v-model="profile.google_chat_webhook" 
                type="url" 
                placeholder="https://chat.googleapis.com/v1/spaces/..." 
              />
              <small>
                Get instant notifications in Google Chat. 
                <a href="#" @click.prevent="showWebhookHelp = !showWebhookHelp" class="help-link">
                  {{ showWebhookHelp ? 'Hide' : 'How to get webhook URL?' }}
                </a>
              </small>
              <div v-if="showWebhookHelp" class="webhook-help">
                <p><strong>Steps to get your webhook URL:</strong></p>
                <ol>
                  <li>Open <a href="https://chat.google.com" target="_blank">Google Chat</a></li>
                  <li>Create a new space or open existing one</li>
                  <li>Click space name → <strong>Apps & integrations</strong></li>
                  <li>Click <strong>Manage webhooks</strong> → <strong>Add webhook</strong></li>
                  <li>Name it "ParkEase" and click <strong>Save</strong></li>
                  <li>Copy the webhook URL and paste it above</li>
                </ol>
              </div>
            </div>
          </label>

          <div class="form-divider"></div>

          <h4>Change Password (Optional)</h4>
          <label>
            Current Password:
            <input v-model="profileForm.current_password" type="password"
              placeholder="Enter current password to make changes" />
          </label>

          <label>
            New Password:
            <input v-model="profileForm.new_password" type="password"
              placeholder="Leave blank to keep current password" />
          </label>

          <div v-if="profileError" class="error-message">{{ profileError }}</div>
          <div v-if="profileSuccess" class="success-message">{{ profileSuccess }}</div>

          <div class="modal-actions">
            <button type="submit" :disabled="profileUpdating" class="save-profile-btn">
              {{ profileUpdating ? 'Updating...' : 'Save Changes' }}
            </button>
            <button type="button" @click="closeProfileEditModal" class="cancel-profile-btn">
              Cancel
            </button>
          </div>
        </form>
      </Modal>

      <!-- Booking Details Modal - Redesigned -->
      <Modal :show="showBookingDetailsModal" title="" @close="closeBookingDetailsModal" hide-actions>
        <div v-if="selectedBooking" class="booking-details-clean">
          <!-- Header with Booking ID and Status -->
          <div class="detail-header-clean">
            <div class="header-left">
              <span class="booking-id-clean">{{ selectedBooking.bookingId }}</span>
              <span class="status-badge-clean" :class="'status-' + (selectedBooking.status || '').toLowerCase().replace(' ', '-')">
                {{ selectedBooking.status }}
              </span>
            </div>
          </div>

          <!-- Main Details Grid -->
          <div class="details-grid-clean">
            <div class="detail-card-clean">
              <div class="detail-icon-clean">
                <i class="fas fa-map-marker-alt"></i>
              </div>
              <div class="detail-content-clean">
                <span class="detail-label-clean">Location</span>
                <span class="detail-value-clean">{{ selectedBooking.lotName }}</span>
              </div>
            </div>

            <div class="detail-card-clean">
              <div class="detail-icon-clean">
                <i class="fas fa-parking"></i>
              </div>
              <div class="detail-content-clean">
                <span class="detail-label-clean">Spot</span>
                <span class="detail-value-clean">{{ selectedBooking.spotNumber }}</span>
              </div>
            </div>

            <div class="detail-card-clean">
              <div class="detail-icon-clean">
                <i class="fas fa-car"></i>
              </div>
              <div class="detail-content-clean">
                <span class="detail-label-clean">Vehicle</span>
                <span class="detail-value-clean">{{ selectedBooking.vehicleNumber }}</span>
              </div>
            </div>

            <div class="detail-card-clean">
                <div class="detail-icon-clean">
                    <i class="fas fa-calendar-alt"></i>
                </div>
                <div class="detail-content-clean">
                    <span class="detail-label-clean">Expected Arrival</span>
                    <span class="detail-value-clean">{{ selectedBooking.scheduledTime }}</span>
                </div>
            </div>

            <div class="detail-card-clean">
                <div class="detail-icon-clean">
                    <i class="fas fa-sign-in-alt"></i>
                </div>
                <div class="detail-content-clean">
                    <span class="detail-label-clean">Check-In</span>
                    <span class="detail-value-clean">{{ selectedBooking.checkInTime }}</span>
                </div>
            </div>

            <div class="detail-card-clean">
                <div class="detail-icon-clean">
                    <i class="fas fa-sign-out-alt"></i>
                </div>
                <div class="detail-content-clean">
                    <span class="detail-label-clean">Check-Out</span>
                    <span class="detail-value-clean">{{ selectedBooking.checkOutTime }}</span>
                </div>
            </div>

            <div v-if="selectedBooking.status !== 'Cancelled' && selectedBooking.status !== 'Rejected'" class="detail-card-clean cost-card">
              <div class="detail-icon-clean">
                <i class="fas fa-rupee-sign"></i>
              </div>
              <div class="detail-content-clean">
                <span class="detail-label-clean">Amount</span>
                <span class="detail-value-clean cost-value">{{ selectedBooking.cost }}</span>
              </div>
            </div>
          </div>

          <!-- Payment Status (for Parked Out bookings) -->
          <div v-if="selectedBooking.status === 'Parked Out'" class="payment-section-clean">
            <div v-if="selectedBooking.paymentStatus === 'paid'" class="payment-status-clean paid">
              <i class="fas fa-check-circle"></i>
              <span>Payment Completed</span>
            </div>
            <div v-else class="payment-status-clean unpaid">
              <i class="fas fa-exclamation-triangle"></i>
              <span>Payment Pending</span>
              <button @click="makePayment(selectedBooking)" class="btn-pay-clean">
                Pay Now
              </button>
            </div>
          </div>

          <!-- Review Section (for Parked Out bookings) -->
          <div v-if="selectedBooking.status === 'Parked Out'" class="review-section-clean">
            <div v-if="selectedBooking.ratingValue" class="review-display-clean">
              <div class="rating-stars-clean">
                {{ '★'.repeat(selectedBooking.ratingValue) }}{{ '☆'.repeat(5 - selectedBooking.ratingValue) }}
              </div>
              <p v-if="selectedBooking.review" class="review-comment-clean">{{ selectedBooking.review }}</p>
            </div>
            <div v-else class="review-prompt-clean">
              <span>How was your experience?</span>
              <button @click="leaveReview(selectedBooking)" class="btn-review-clean">
                <i class="fas fa-star"></i> Leave Review
              </button>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="actions-clean">
            <button v-if="selectedBooking.status === 'Confirmed'" @click="cancelBooking(selectedBooking.id)" class="btn-action-clean btn-cancel">
              <i class="fas fa-times"></i> Cancel
            </button>
            <button v-if="['Parked Out', 'Cancelled', 'Rejected'].includes(selectedBooking.status)" @click="rebookParking(selectedBooking)" class="btn-action-clean btn-rebook">
              <i class="fas fa-redo"></i> Rebook
            </button>
            <button @click="downloadBooking(selectedBooking)" class="btn-action-clean btn-download">
              <i class="fas fa-download"></i> Download
            </button>
          </div>
        </div>
      </Modal>

      <!-- Payment Modal -->
      <PaymentModal
        :show="showPaymentModal"
        :reservation-id="paymentData.reservationId"
        :booking-id="paymentData.bookingId"
        :amount="paymentData.amount"
        :duration-hours="paymentData.durationHours"
        @payment-success="handlePaymentSuccess"
        @close="closePaymentModal"
      />

      <!-- Review Modal -->
      <Modal :show="showReviewModal" title="Leave a Review" @close="closeReviewModal" hide-actions>
        <form @submit.prevent="submitReview" class="review-form">
          <div class="review-header">
            <h3>{{ reviewForm.lotName }}</h3>
            <p>How was your parking experience?</p>
          </div>

          <div class="rating-input">
            <label>Rating</label>
            <div class="star-rating">
              <button 
                v-for="star in 5" 
                :key="star" 
                type="button"
                @click="reviewForm.rating = star"
                class="star-btn"
                :class="{ 'active': star <= reviewForm.rating }"
              >
                <i class="fas fa-star"></i>
              </button>
            </div>
            <span class="rating-text">{{ reviewForm.rating }} out of 5 stars</span>
          </div>

          <div class="comment-input">
            <label>Comments (Optional)</label>
            <textarea 
              v-model="reviewForm.comment" 
              rows="4" 
              placeholder="Share your experience..."
            ></textarea>
          </div>

          <div class="modal-actions">
            <button type="submit" class="submit-review-btn">
              <i class="fas fa-paper-plane"></i> Submit Review
            </button>
            <button type="button" @click="closeReviewModal" class="skip-review-btn">
              Skip for Now
            </button>
          </div>
        </form>
      </Modal>
    </div>
  </div>
</template>

<style scoped>
@import '@/assets/styles/UserDashboard.css';
</style>

<script>
import Modal from '@/components/common/Modal.vue';
import DataTable from '@/components/common/DataTable.vue';
import Chart from '@/components/common/Chart.vue';
import Toast from '@/components/common/Toast.vue';
import PaymentModal from '@/components/user/PaymentModal.vue';
import { userApi } from '@/utils/api';
import { useCrud } from '@/composables/useCrud';

export default {
  name: "UserDashboard",
  components: {
    Modal,
    DataTable,
    Chart,
    Toast,
    PaymentModal
  },
  setup() {
    // Vehicle CRUD setup
    const vehicleApi = {
      getAll: userApi.getVehicles,
      create: userApi.addVehicle,
      update: userApi.updateVehicle,
      delete: userApi.deleteVehicle
    };

    const vehicleCrud = useCrud(vehicleApi, {
      defaultForm: {
        id: null,
        vehicle_number: '',
        vehicle_name: '',
        color: ''
      },
      mapResponse: (data) => data.map(vehicle => ({
        id: vehicle.id,
        vehicle_number: vehicle.vehicle_number,
        vehicle_name: vehicle.vehicle_name,
        color: vehicle.color
      })),
      mapRequest: (form) => ({
        vehicle_number: form.vehicle_number,
        vehicle_name: form.vehicle_name,
        color: form.color
      }),
      onSuccess: async (action, data) => {
        window.dispatchEvent(new CustomEvent('showToast', { 
          detail: { 
            message: data.message || `Vehicle ${action}ed successfully!`,
            type: 'success'
          }
        }));
        // Refresh profile to update completion status after vehicle operations
        try {
          const profileResponse = await userApi.getProfile();
          // We need to emit an event or use a different approach since we can't directly access 'this' in setup
          window.dispatchEvent(new CustomEvent('refreshProfile', { detail: profileResponse }));
        } catch (err) {
          console.error('Error refreshing profile after vehicle operation:', err);
        }
      },
      onError: (action, error) => {
        window.dispatchEvent(new CustomEvent('showToast', { 
          detail: { 
            message: error.message || `Failed to ${action} vehicle`,
            type: 'error'
          }
        }));
      }
    });

    return {
      vehicleCrud
    };
  },
  data() {
    return {
      activeTab: this.$route.query.tab || "home",
      bookings: [],
      lots: [],
      allLots: [], // Store all lots for search
      searchQuery: '',
      profile: {
        id: null,
        email: "",
        username: "",
        first_name: "",
        last_name: "",
        phone_number: "",
        address: "",
        pincode: "",
        google_chat_webhook: "",
        created_at: null,
        profile_completion: 0,
        can_book: false,
        missing_fields: [],
        has_vehicles: false
      },
      showProfileBanner: false,
      profileLoaded: false, // Track if profile has been loaded
      showWebhookHelp: false, // Show/hide webhook help
      // Profile management
      profileForm: {
        current_password: "",
        new_password: ""
      },
      profileError: "",
      profileSuccess: "",
      profileUpdating: false,
      // Delete account
      showDeleteAccountModal: false,
      deleteForm: {
        password: "",
        confirmation: ""
      },
      deleteError: "",
      deleting: false,
      // Booking modal state
      showAddBookingModal: false,
      showEditBookingModal: false,
      bookingForm: {
        id: null,
        lotId: "",
        vehicle_id: "",
        expected_arrival: "",
        expected_departure: "",
        startTime: "",
        endTime: ""
      },
      bookingData: {
        lot: {},
        vehicles: [],
        has_vehicles: false,
        has_active_reservation: false
      },
      // User Analytics
      userAnalytics: {
        overview: {},
        monthly_spending: [],
        favorite_lots: [],
        weekly_activity: [],
        recent_activity: []
      },
      // Home Dashboard Data
      currentlyParked: null,
      upcomingBooking: null,
      featuredLots: [],
      recentHistory: [],
      // Favorites
      favoriteLotIds: [],
      taskLoading: false,
      taskResult: null,
      taskError: null,
      // Lot Details Modal
      showLotDetailsModal: false,
      selectedLot: null,
      // History Pagination
      historyPage: 1,
      historyPerPage: 5,
      fullHistory: [],
      historySortBy: 'date', // 'date', 'cost', 'duration'
      // Profile Edit Modal
      showProfileEditModal: false,
      // Booking Details Modal
      showBookingDetailsModal: false,
      selectedBooking: null,
      // Review Modal
      showReviewModal: false,
      reviewForm: {
        reservationId: null,
        lotId: null,
        lotName: '',
        rating: 5,
        comment: ''
      },
      // Payment Modal
      showPaymentModal: false,
      paymentData: {
        reservationId: null,
        bookingId: '',
        amount: 0,
        durationHours: 0
      },
      // Live duration timer
      currentTime: new Date(),
      durationTimer: null
    };
  },
  computed: {
    liveParkingDuration() {
      if (!this.currentlyParked || !this.currentlyParked.parking_timestamp) {
        return 'Unknown';
      }
      
      const start = new Date(this.currentlyParked.parking_timestamp);
      const now = this.currentTime;
      const diffMs = now - start;

      const hours = Math.floor(Math.abs(diffMs) / (1000 * 60 * 60));
      const minutes = Math.floor((Math.abs(diffMs) % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      } else {
        return `${minutes}m`;
      }
    },
    // Column definitions for different booking tables
    confirmedBookingColumns() {
      return [
        { key: 'bookingId', label: 'Booking ID' },
        { key: 'lotName', label: 'Parking Lot' },
        { key: 'spotNumber', label: 'Spot' },
        { key: 'vehicleNumber', label: 'Vehicle' },
        { key: 'scheduledTime', label: 'Scheduled' }
      ];
    },
    pendingBookingColumns() {
      return [
        { key: 'bookingId', label: 'Booking ID' },
        { key: 'lotName', label: 'Parking Lot' },
        { key: 'vehicleNumber', label: 'Vehicle' },
        { key: 'requestedTime', label: 'Requested Time' }
      ];
    },
    cancelledBookingColumns() {
      return [
        { key: 'bookingId', label: 'Booking ID' },
        { key: 'lotName', label: 'Parking Lot' },
        { key: 'status', label: 'Status' },
        { key: 'reason', label: 'Reason' }
      ];
    },
    historyBookingColumns() {
      return [
        { key: 'bookingId', label: 'Booking ID' },
        { key: 'entryTime', label: 'Entry Time' },
        { key: 'exitTime', label: 'Exit Time' },
        { key: 'amount', label: 'Amount' },
        { key: 'rating', label: 'Rating' }
      ];
    },
    lotColumns() {
      return [
        { key: 'id', label: 'ID' },
        { key: 'name', label: 'Name' },
        { key: 'location', label: 'Location' },
        { key: 'capacity', label: 'Capacity' },
        { key: 'availableSpots', label: 'Available Spots' }
      ];
    },
    vehicleColumns() {
      return [
        { key: 'id', label: 'ID' },
        { key: 'vehicle_number', label: 'Number' },
        { key: 'vehicle_name', label: 'Name' },
        { key: 'color', label: 'Color' }
      ];
    },
    favoriteLotColumns() {
      return [
        { key: 'name', label: 'Location' },
        { key: 'usage_count', label: 'Usage Count' },
        { key: 'total_spent', label: 'Total Spent', formatter: (value) => `₹${value}` }
      ];
    },
    recentActivityColumns() {
      return [
        { key: 'lot_name', label: 'Location' },
        { key: 'start', label: 'Date', formatter: (value) => new Date(value).toLocaleDateString() },
        { key: 'status', label: 'Status' },
        { key: 'cost', label: 'Cost', formatter: (value) => value ? `₹${this.formatInteger(value)}` : 'N/A' }
      ];
    },
    spendingChartData() {
      return {
        labels: this.userAnalytics.monthly_spending?.map(d => {
          // Convert YYYY-MM to readable format like "Jan 2024"
          const [year, month] = d.month.split('-');
          const date = new Date(year, parseInt(month) - 1);
          return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        }) || [],
        data: this.userAnalytics.monthly_spending?.map(d => d.spent) || []
      };
    },
    weeklyChartData() {
      return {
        labels: this.userAnalytics.weekly_activity?.map(d => new Date(d.date).toLocaleDateString()) || [],
        data: this.userAnalytics.weekly_activity?.map(d => d.bookings) || []
      };
    },
    historyColumns() {
      return [
        { key: 'id', label: 'ID' },
        { key: 'lotName', label: 'Lot' },
        { key: 'vehicleNumber', label: 'Vehicle' },
        { key: 'startTime', label: 'Parked' },
        { key: 'endTime', label: 'Left' },
        { key: 'cost', label: 'Cost' }
      ];
    },
    // Computed properties for different booking categories
    upcomingBookings() {
      return this.bookings
        .filter(booking => booking.status === 'Confirmed')
        .sort((a, b) => new Date(a.startTime) - new Date(b.startTime));
    },
    pendingBookings() {
      return this.bookings.filter(booking => booking.status === 'Pending');
    },
    cancelledBookings() {
      return this.bookings.filter(booking =>
        booking.status === 'Cancelled' || booking.status === 'Rejected'
      );
    },
    historyBookings() {
      return this.bookings
        .filter(booking => booking.status === 'Parked Out' || booking.status === 'Completed')
        .sort((a, b) => new Date(b.endTime) - new Date(a.endTime));
    },
    favoriteLots() {
      return this.lots.filter(lot => lot.isFavorite);
    },
    profileHistoryColumns() {
      return [
        { key: 'bookingId', label: 'Booking ID' },
        { key: 'date', label: 'Date' },
        { key: 'lot_name', label: 'Location' },
        { key: 'vehicle_number', label: 'Vehicle' },
        { key: 'status', label: 'Status' },
        { key: 'duration', label: 'Duration' },
        { key: 'parking_cost', label: 'Cost', formatter: (value) => value !== null ? `₹${this.formatInteger(value)}` : 'N/A' },
        { key: 'rating', label: 'Rating' }
      ];
    },
    sortedHistory() {
      const sorted = [...this.fullHistory];
      
      if (this.historySortBy === 'date') {
        sorted.sort((a, b) => new Date(b.parking_timestamp) - new Date(a.parking_timestamp));
      } else if (this.historySortBy === 'cost') {
        sorted.sort((a, b) => (b.parking_cost || 0) - (a.parking_cost || 0));
      } else if (this.historySortBy === 'duration') {
        sorted.sort((a, b) => (b.duration_minutes || 0) - (a.duration_minutes || 0));
      }
      
      return sorted;
    },
    paginatedHistory() {
      const start = (this.historyPage - 1) * this.historyPerPage;
      const end = start + this.historyPerPage;
      return this.sortedHistory.slice(start, end);
    },
    totalHistoryPages() {
      return Math.ceil(this.fullHistory.length / this.historyPerPage);
    },
    topLocations() {
      const locationMap = {};
      this.fullHistory.forEach(history => {
        if (!locationMap[history.lot_name]) {
          locationMap[history.lot_name] = { name: history.lot_name, visits: 0, spent: 0 };
        }
        locationMap[history.lot_name].visits++;
        locationMap[history.lot_name].spent += history.parking_cost || 0;
      });
      
      return Object.values(locationMap)
        .sort((a, b) => b.visits - a.visits)
        .slice(0, 5);
    },
    averageDuration() {
      if (this.fullHistory.length === 0) return '0m';
      const totalMinutes = this.fullHistory.reduce((sum, h) => sum + (h.duration_minutes || 0), 0);
      const avg = Math.floor(totalMinutes / this.fullHistory.length);
      const hours = Math.floor(avg / 60);
      const minutes = avg % 60;
      return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
    },
    mostCommonDay() {
      if (this.fullHistory.length === 0) return 'N/A';
      const dayCount = {};
      this.fullHistory.forEach(h => {
        const day = new Date(h.parking_timestamp).toLocaleDateString('en-US', { weekday: 'long' });
        dayCount[day] = (dayCount[day] || 0) + 1;
      });
      return Object.keys(dayCount).reduce((a, b) => dayCount[a] > dayCount[b] ? a : b, 'N/A');
    },
    preferredTime() {
      if (this.fullHistory.length === 0) return 'N/A';
      const hourCount = {};
      this.fullHistory.forEach(h => {
        const hour = new Date(h.parking_timestamp).getHours();
        const period = hour < 12 ? 'Morning' : hour < 17 ? 'Afternoon' : 'Evening';
        hourCount[period] = (hourCount[period] || 0) + 1;
      });
      return Object.keys(hourCount).reduce((a, b) => hourCount[a] > hourCount[b] ? a : b, 'N/A');
    },
    averageCostPerVisit() {
      if (this.fullHistory.length === 0) return '0';
      const total = this.fullHistory.reduce((sum, h) => sum + (h.parking_cost || 0), 0);
      return this.formatInteger(total / this.fullHistory.length);
    }
  },
  created() {
    this.fetchBookings();
    this.fetchLots();
    this.fetchProfile();
    this.vehicleCrud.fetchItems();
    this.fetchUserAnalytics(); // Fetch analytics data on component load
    this.fetchHomeData(); // Fetch home dashboard data

    // Listen for profile refresh events
    window.addEventListener('refreshProfile', this.handleProfileRefresh);
    
    // Start live duration timer
    this.durationTimer = setInterval(() => {
      this.currentTime = new Date();
    }, 60000); // Update every minute
  },
  beforeUnmount() {
    // Clean up event listener
    window.removeEventListener('refreshProfile', this.handleProfileRefresh);
    
    // Clear duration timer
    if (this.durationTimer) {
      clearInterval(this.durationTimer);
    }
  },
  watch: {
    activeTab(newTab) {
      // Update URL query parameter to persist tab state
      this.$router.replace({ query: { ...this.$route.query, tab: newTab } });

      if (newTab === 'analytics') {
        this.fetchUserAnalytics();
      } else if (newTab === 'home') {
        this.fetchHomeData();
      } else if (newTab === 'profile') {
        this.fetchUserAnalytics(); // Fetch analytics for profile stats
      }
    }
  },
  methods: {
    formatInteger(value) {
      if (value === null || value === undefined) return '0';
      return Math.trunc(value);
    },
    getTabTitle() {
      const titles = {
        'home': 'Dashboard Home',
        'bookings': 'My Bookings',
        'lots': 'Explore Parking Lots',
        'profile': 'My Profile',
        'analytics': 'My Analytics'
      };
      return titles[this.activeTab] || 'Dashboard';
    },

    getWelcomeMessage() {
      if (this.activeTab === 'home') {
        const name = this.profile.first_name || 'Parker';
        
        if (this.fullHistory && this.fullHistory.length > 0) {
            const hasCompletedBookings = this.fullHistory.some(
              booking => booking.status === 'Parked Out' || booking.status === 'Completed'
            );

            if (hasCompletedBookings) {
              return `Welcome back, ${name}!`;
            }
        }
        
        // This covers:
        // 1. New users (history is empty or not loaded yet).
        // 2. Existing users with no completed bookings.
        return `Welcome, ${name}!`;
      }
      return '';
    },

    // Home Dashboard Methods
    async fetchHomeData() {
      try {
        await Promise.all([
          this.fetchCurrentlyParked(),
          this.fetchUpcomingBooking(),
          this.fetchFeaturedLots(),
          this.fetchRecentHistory()
        ]);
      } catch (err) {
        console.error('Error fetching home data:', err);
      }
    },

    async fetchCurrentlyParked() {
      try {
        const reservations = await userApi.getReservations();
        // Find reservation that has start time but no end time (currently parked)
        const parked = reservations.find(r => r.start && !r.end);

        if (parked) {
          // Get additional details for the parked vehicle
          const [vehicles, lots] = await Promise.all([
            userApi.getVehicles(),
            userApi.getParkingLots()
          ]);

          const vehicle = vehicles.find(v => v.id === parked.vehicle_id);
          const lot = lots.find(l => l.id === parked.lot_id);

          this.currentlyParked = {
            id: parked.id,
            vehicle_number: vehicle?.vehicle_number || 'Unknown',
            lot_name: lot?.location || 'Unknown Location',
            spotNumber: reservation.spot_number 
              ? `#${reservation.spot_number}` 
              : (reservation.spot_id ? `#${reservation.spot_id}` : 'TBD'),            parking_timestamp: parked.start,
            status: 'Parked'
          };
        } else {
          this.currentlyParked = null;
        }
      } catch (err) {
        console.error('Error fetching currently parked:', err);
        this.currentlyParked = null;
      }
    },

    async fetchUpcomingBooking() {
      try {
        const reservations = await userApi.getReservations();
        // Find confirmed reservation that hasn't started yet (no parking_timestamp)
        const upcoming = reservations.find(r => 
          r.status === 'Confirmed' && !r.start && !r.parking_timestamp
        );

        if (upcoming) {
          const [vehicles, lots] = await Promise.all([
            userApi.getVehicles(),
            userApi.getParkingLots()
          ]);

          const vehicle = vehicles.find(v => v.id === upcoming.vehicle_id);
          const lot = lots.find(l => l.id === upcoming.lot_id);

          this.upcomingBooking = {
            id: upcoming.id,
            bookingId: upcoming.booking_id || `BK-${upcoming.id}`,
            lot_name: lot?.location || lot?.prime_location_name || 'Unknown Location',
            vehicle_number: vehicle?.vehicle_number || 'Unknown Vehicle',
            expected_arrival: upcoming.expected_arrival,
            expected_departure: upcoming.expected_departure,
            status: upcoming.status
          };
        } else {
          this.upcomingBooking = null;
        }
      } catch (err) {
        console.error('Error fetching upcoming booking:', err);
        this.upcomingBooking = null;
      }
    },

    async fetchFeaturedLots() {
      try {
        const data = await userApi.getParkingLots();
        // Map data with same structure as main lots and show lots with available spots
        this.featuredLots = data
          .map(lot => ({
            id: lot.id,
            name: lot.location,
            location: lot.address || lot.location,
            capacity: lot.total_spots,
            availableSpots: lot.available_spots || lot.total_spots,
            price: lot.price || 'N/A',
            available_from: lot.available_from,
            available_to: lot.available_to,
            operatingHours: lot.available_from && lot.available_to
              ? `${lot.available_from} - ${lot.available_to}`
              : '24/7',
            isActive: lot.is_active !== false, // Active based on is_active field only
            isFavorite: false
          }))
          .filter(lot => lot.availableSpots > 0)
          .sort((a, b) => b.availableSpots - a.availableSpots)
          .slice(0, 8); // Show more lots since it's scrollable now
      } catch (err) {
        console.error('Error fetching featured lots:', err);
        this.featuredLots = [];
      }
    },

    async fetchRecentHistory() {
      try {
        const reservations = await userApi.getReservations();
        // Filter completed reservations (those with both start and end times)
        const completed = reservations
          .filter(r => r.start && r.end)
          .sort((a, b) => new Date(b.end) - new Date(a.end));

        if (completed.length > 0) {
          // Get additional details for recent history
          const [vehicles, lots] = await Promise.all([
            userApi.getVehicles(),
            userApi.getParkingLots()
          ]);

          this.recentHistory = completed.slice(0, 10).map(reservation => {
            const vehicle = vehicles.find(v => v.id === reservation.vehicle_id);
            const lot = lots.find(l => l.id === reservation.lot_id);

            return {
              id: reservation.id,
              bookingId: reservation.booking_id || `BOOK-${reservation.id}`,
              vehicle_number: vehicle?.vehicle_number || 'Unknown',
              lot_name: lot?.location || 'Unknown Location',
              parking_timestamp: reservation.start,
              leaving_timestamp: reservation.end,
              parking_cost: reservation.cost,
              status: 'Completed',
              rating: reservation.rating
            };
          });
        } else {
          this.recentHistory = [];
        }
      } catch (err) {
        console.error('Error fetching recent history:', err);
        this.recentHistory = [];
      }
    },

    async parkIn(reservationId) {
      try {
        const response = await userApi.parkIn(reservationId);
        this.showToast(response.message || 'Successfully parked in!', 'success', 'Park In');

        // Refresh all data immediately
        await Promise.all([
          this.fetchHomeData(),
          this.fetchBookings()
        ]);
      } catch (err) {
        console.error('Error parking in:', err);
        this.showToast(err.message || 'Failed to park in. Please try again.', 'error', 'Park In Failed');
        
        // IMPORTANT: Refresh data even on error because the booking status may have changed
        // (e.g., rejected for being too late)
        await Promise.all([
          this.fetchHomeData(),
          this.fetchBookings()
        ]);
      }
    },

    async parkOut(reservationId) {
      try {
        const response = await userApi.parkOut(reservationId);
        this.showToast(`Park out successful! Final cost: ₹${response.final_cost}`, 'success', 'Park Out');

        // Refresh all data immediately
        await Promise.all([
          this.fetchHomeData(),
          this.fetchBookings(),
          this.fetchUserAnalytics() // Update spending stats
        ]);
        
        // Get the reservation details
        const reservation = await this.getReservationDetails(reservationId);
        
        // Show payment modal with actual parking duration
        this.paymentData = {
          reservationId: reservationId,
          bookingId: reservation.bookingId || 'N/A',
          amount: response.final_cost || 0,
          durationHours: parseFloat(response.duration_hours) || 0
        };
        
        setTimeout(() => {
          this.showPaymentModal = true;
        }, 500);
      } catch (err) {
        console.error('Error parking out:', err);
        this.showToast(err.message || 'Failed to park out. Please try again.', 'error', 'Park Out Failed');
        
        // Refresh data even on error
        await Promise.all([
          this.fetchHomeData(),
          this.fetchBookings()
        ]);
      }
    },

    async getReservationDetails(reservationId) {
      try {
        // Find the reservation in bookings
        const booking = this.bookings.find(b => b.id === reservationId);
        if (booking) {
          return {
            id: reservationId,
            lotId: booking.lot_id,
            lotName: booking.lotName,
            bookingId: booking.bookingId || booking.booking_id
          };
        }
        return { id: reservationId, lotId: null, lotName: 'Unknown Location', bookingId: 'N/A' };
      } catch (err) {
        console.error('Error getting reservation details:', err);
        return { id: reservationId, lotId: null, lotName: 'Unknown Location', bookingId: 'N/A' };
      }
    },

    openReviewModal(reservation) {
      this.reviewForm = {
        reservationId: reservation.id,
        lotId: reservation.lotId,
        lotName: reservation.lotName,
        rating: 5,
        comment: ''
      };
      this.showReviewModal = true;
    },

    closeReviewModal() {
      this.showReviewModal = false;
      this.reviewForm = {
        reservationId: null,
        lotId: null,
        lotName: '',
        rating: 5,
        comment: ''
      };
    },

    // Payment Modal Methods
    async handlePaymentSuccess(paymentResponse) {
      this.showToast(`Payment successful! ₹${paymentResponse.payment.amount} paid`, 'success', 'Payment Complete');
      
      // Close payment modal
      this.showPaymentModal = false;
      
      // Refresh data
      await Promise.all([
        this.fetchHomeData(),
        this.fetchBookings(),
        this.fetchUserAnalytics()
      ]);
      
      // Get reservation details
      const reservation = await this.getReservationDetails(this.paymentData.reservationId);
      
      // Check if review already exists for this parking lot
      const hasReview = await this.checkIfReviewExists(reservation.lotId);
      
      // Only show review modal if no review exists
      if (!hasReview) {
        setTimeout(() => {
          this.openReviewModal(reservation);
        }, 500);
      }
    },

    async closePaymentModal() {
      this.showPaymentModal = false;
      // Still show review modal even if payment is skipped
      // Get proper reservation details
      const reservation = await this.getReservationDetails(this.paymentData.reservationId);
      
      // Check if review already exists for this parking lot
      const hasReview = await this.checkIfReviewExists(reservation.lotId);
      
      // Only show review modal if no review exists
      if (!hasReview) {
        setTimeout(() => {
          this.openReviewModal(reservation);
        }, 300);
      }
    },

    async checkIfReviewExists(lotId) {
      if (!lotId) return false;
      
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/user/reviews/check/${lotId}`, {
          headers: { 'auth-token': token }
        });
        
        if (response.ok) {
          const data = await response.json();
          return data.has_review || false;
        }
        return false;
      } catch (err) {
        console.error('Error checking review:', err);
        return false;
      }
    },

    async submitReview() {
      // Validate required fields
      if (!this.reviewForm.lotId) {
        this.showToast('Unable to submit review. Parking lot information is missing.', 'error', 'Review Failed');
        return;
      }
      
      if (!this.reviewForm.rating || this.reviewForm.rating < 1 || this.reviewForm.rating > 5) {
        this.showToast('Please select a rating between 1 and 5 stars.', 'error', 'Invalid Rating');
        return;
      }
      
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/user/reviews', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          },
          body: JSON.stringify({
            parking_lot_id: this.reviewForm.lotId,
            rating: this.reviewForm.rating,
            comment: this.reviewForm.comment || ''
          })
        });
        
        if (response.ok) {
          this.showToast('Thank you for your feedback!', 'success', 'Review Submitted');
          this.closeReviewModal();
          
          // Refresh bookings to show the new review
          await this.fetchBookings();
        } else {
          const error = await response.json();
          this.showToast(error.error || 'Failed to submit review', 'error', 'Review Failed');
        }
      } catch (err) {
        console.error('Error submitting review:', err);
        this.showToast('Failed to submit review. Please try again.', 'error', 'Review Failed');
      }
    },

    calculateParkingDuration(startTime) {
      if (!startTime) return 'Unknown';

      const start = new Date(startTime);
      const now = new Date();
      const diffMs = now - start;

      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      } else {
        return `${minutes}m`;
      }
    },

    formatDateTime(dateTimeStr) {
      if (!dateTimeStr) return 'N/A';
      const date = new Date(dateTimeStr);
      return date.toLocaleString();
    },

    formatTimeOnly(dateTimeStr) {
      if (!dateTimeStr) return 'N/A';
      const date = new Date(dateTimeStr);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },

    formatDate(dateStr) {
      if (!dateStr) return 'N/A';
      const date = new Date(dateStr);
      return date.toLocaleDateString();
    },

    handleProfileRefresh(event) {
      if (event.detail) {
        this.profile = { ...this.profile, ...event.detail };
      }
    },

    // CRUD for Bookings
    async fetchBookings() {
      try {
        const data = await userApi.getReservations();

        // Get additional details for better display
        const [vehicles, lots] = await Promise.all([
          userApi.getVehicles(),
          userApi.getParkingLots()
        ]);

        this.bookings = data.map(reservation => {
          const vehicle = vehicles.find(v => v.id === reservation.vehicle_id);
          const lot = lots.find(l => l.id === reservation.lot_id);

          // Debug logging
          console.log('Reservation:', reservation.id);
          console.log('  Vehicle ID:', reservation.vehicle_id, 'Found:', vehicle);
          console.log('  Expected Arrival:', reservation.expected_arrival);
          console.log('  Status:', reservation.status);

          // Determine status based on reservation state
          let status = 'Pending'; // Default status
          if (reservation.status) {
            status = reservation.status;
          } else if (reservation.start && reservation.end) {
            status = 'Parked Out'; // Completed reservation
          } else if (reservation.start && !reservation.end) {
            status = 'Confirmed'; // Currently parked
          } else if (!reservation.start) {
            status = 'Confirmed'; // Upcoming booking
          }

          return {
            id: reservation.id,
            lot_id: reservation.lot_id,  // Add lot_id for review submission
            bookingId: reservation.booking_id || `BOOK-${reservation.id}`,
            lotName: lot?.location || lot?.prime_location_name || `Lot #${reservation.lot_id}`,
            
            spotNumber: reservation.spot_number 
              ? `#${reservation.spot_number}` 
              : (reservation.spot_id ? `#${reservation.spot_id}` : 'TBD'),
            
              startTime: reservation.expected_arrival 
              ? new Date(reservation.expected_arrival).toLocaleString() 
              : 'TBD',
            
            endTime: reservation.end ? new Date(reservation.end).toLocaleString() :reservation.expected_departure ? new Date(reservation.expected_departure).toLocaleString() : 'TBD',
            
            status: status,
            
            cost: reservation.cost ? '₹' + reservation.cost : 'TBD',
            
            vehicleNumber: vehicle?.vehicle_number || 'Unknown Vehicle',
            
            // For confirmed bookings - scheduled time (TIME ONLY)
            scheduledTime: reservation.expected_arrival ? 
              new Date(reservation.expected_arrival).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'TBD',
            
              // For pending bookings - requested time (TIME ONLY)
            requestedTime: reservation.expected_arrival ? 
              new Date(reservation.expected_arrival).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'TBD',
            
              // For cancelled bookings - reason
            reason: reservation.cancellation_reason || 'User cancelled',
            
            // For history - entry and exit times (TIME ONLY)
            entryTime: reservation.start ? 
              new Date(reservation.start).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'N/A',
            exitTime: reservation.end ? 
              new Date(reservation.end).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'N/A',
            
              // For history - amount and rating
            amount: reservation.cost ? '₹' + reservation.cost : 'N/A',
            rating: reservation.rating ? '★'.repeat(reservation.rating) : 'Not rated',
            ratingValue: reservation.rating || null,
            review: reservation.review || null
          };
        });
        
        // Populate full history for profile page - ALL bookings with any status
        this.fullHistory = data
          .map(reservation => {
            const vehicle = vehicles.find(v => v.id === reservation.vehicle_id);
            const lot = lots.find(l => l.id === reservation.lot_id);
            
            // Calculate duration using actual parking times (not expected times)
            let durationStr = 'N/A';
            let durationMinutes = 0;
            
            // For completed bookings, use actual parking_timestamp and leaving_timestamp
            // These are mapped to 'start' and 'end' in the API response
            if (reservation.start && reservation.end) {
              const startTime = new Date(reservation.start);
              const endTime = new Date(reservation.end);
              const durationMs = endTime - startTime;
              durationMinutes = Math.floor(durationMs / (1000 * 60));
              
              // Only show duration if it's positive (actual parking duration)
              if (durationMinutes > 0) {
                const hours = Math.floor(durationMinutes / 60);
                const minutes = durationMinutes % 60;
                durationStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
              } else {
                durationStr = 'N/A';
                durationMinutes = 0;
              }
            }
            
            // Use booking timestamp or expected arrival for date
            const dateToShow = reservation.start || reservation.expected_arrival || reservation.booking_timestamp;
            
            // Only show cost for Parked Out/Completed bookings
            const status = reservation.status || 'Unknown';
            const shouldShowCost = status === 'Parked Out' || status === 'Completed';
            
            return {
              id: reservation.id,
              bookingId: reservation.booking_id || `BOOK-${reservation.id}`,
              date: dateToShow ? new Date(dateToShow).toLocaleDateString() : 'N/A',
              lot_name: lot?.location || 'Unknown Location',
              vehicle_number: vehicle?.vehicle_number || 'Unknown',
              status: status,
              duration: durationStr,
              duration_minutes: durationMinutes,
              parking_timestamp: reservation.start,
              leaving_timestamp: reservation.end,
              parking_cost: shouldShowCost ? (reservation.cost || 0) : null,
              rating: reservation.rating ? '★'.repeat(reservation.rating) : 'Not rated',
              ratingValue: reservation.rating || null,
              review: reservation.review || null
            };
          })
          .sort((a, b) => {
            const dateA = new Date(a.parking_timestamp || a.date);
            const dateB = new Date(b.parking_timestamp || b.date);
            return dateB - dateA;
          });
      } catch (err) {
        console.error('Error fetching bookings:', err);
        this.bookings = [];
        this.fullHistory = [];
      }
    },

    async addBooking() {
      try {
        if (!this.bookingForm.vehicle_id) {
          this.showToast('Please select a vehicle', 'warning', 'Missing Information');
          return;
        }

        if (!this.bookingForm.expected_arrival || !this.bookingForm.expected_departure) {
          this.showToast('Please select expected arrival and departure times', 'warning', 'Missing Information');
          return;
        }

        // Validate that departure is after arrival
        if (this.bookingForm.expected_arrival >= this.bookingForm.expected_departure) {
          this.showToast('Departure time must be after arrival time', 'error', 'Invalid Time');
          return;
        }

        const data = await userApi.bookSpot(this.bookingForm.lotId, {
          vehicle_id: this.bookingForm.vehicle_id,
          expected_arrival: this.bookingForm.expected_arrival,
          expected_departure: this.bookingForm.expected_departure
        });

        this.showToast(data.message || 'Spot booked successfully!', 'success', 'Booking Confirmed');
        await this.fetchBookings();
        await this.fetchLots();
        await this.fetchHomeData(); // Refresh home data
        this.closeBookingModal();
      } catch (err) {
        console.error('Error booking spot:', err);

        // Check if it's a profile completion error
        const errorMessage = err.message || 'Error booking spot. Please try again.';
        const isProfileError = errorMessage.includes('Please complete your profile') ||
          errorMessage.includes('First name is required') ||
          errorMessage.includes('Last name is required') ||
          errorMessage.includes('Phone number is required');

        if (isProfileError) {
          // Show error message and redirect to profile tab
          this.showToast(errorMessage + ' Redirecting you to the Profile tab.', 'error', 'Profile Incomplete', 5000);
          setTimeout(() => {
            this.activeTab = 'profile';
            this.closeBookingModal();
          }, 1000);
        } else {
          // Regular error handling
          this.showToast(errorMessage, 'error', 'Booking Failed');
        }
      }
    },

    editBooking(booking) {
      this.showEditBookingModal = true;
      this.showAddBookingModal = false;
      const lot = this.lots.find(l => l.name === booking.lotName);
      this.bookingForm = {
        id: booking.id,
        lotId: lot ? lot.id : "",
        startTime: booking.startTime,
        endTime: booking.endTime
      };
    },

    updateBooking() {
      // TODO: Replace with API call
      const idx = this.bookings.findIndex(b => b.id === this.bookingForm.id);
      const lot = this.lots.find(l => l.id === this.bookingForm.lotId);
      if (idx !== -1) {
        this.bookings[idx] = {
          ...this.bookings[idx],
          lotName: lot ? lot.name : "",
          startTime: this.bookingForm.startTime,
          endTime: this.bookingForm.endTime
        };
      }
      this.closeBookingModal();
    },

    async deleteBooking(id) {
      try {
        // Show confirmation via toast (user can still use browser confirm for critical actions)
        if (!confirm('Are you sure you want to cancel this booking? This action cannot be undone.')) {
          return;
        }

        // Find the booking to cancel
        const bookingToCancel = this.bookings.find(b => b.id === id);
        if (!bookingToCancel) {
          this.showToast('Booking not found.', 'error', 'Error');
          return;
        }

        // For now, we'll simulate the API call by updating the booking status locally
        // In a real implementation, this would be an API call to cancel the reservation
        const bookingIndex = this.bookings.findIndex(b => b.id === id);
        if (bookingIndex !== -1) {
          // Update the booking status to 'Cancelled'
          this.bookings[bookingIndex] = {
            ...this.bookings[bookingIndex],
            status: 'Cancelled'
          };
          
          this.showToast('Booking cancelled successfully. It will now appear in the Cancelled/Rejected section.', 'success', 'Booking Cancelled');
        }

        // TODO: Replace with actual API call
        // await userApi.cancelReservation(id);
        
      } catch (err) {
        console.error('Error cancelling booking:', err);
        this.showToast('Error cancelling booking. Please try again.', 'error', 'Cancellation Failed');
      }
    },

    closeBookingModal() {
      this.showAddBookingModal = false;
      this.showEditBookingModal = false;
      this.bookingForm = {
        id: null,
        lotId: "",
        vehicle_id: "",
        expected_arrival: "",
        expected_departure: "",
        startTime: "",
        endTime: ""
      };
      this.bookingData = {
        lot: {},
        vehicles: [],
        has_vehicles: false,
        has_active_reservation: false
      };
    },

    openBookingModal() {
      // Check if profile is complete before allowing booking
      if (!this.profile.can_book || this.profile.profile_completion < 100) {
        this.showToast('Please complete your profile before booking. Missing: ' + (this.profile.missing_fields || []).join(', '), 'warning', 'Profile Incomplete', 5000);
        this.activeTab = 'profile';
        this.showProfileBanner = true;
        return;
      }
      this.showAddBookingModal = true;
    },

    openBookModalForLot(lot) {
      // Validate lot exists
      if (!lot || !lot.id) {
        this.showToast('Invalid parking lot selected. Please try again.', 'error', 'Error');
        return;
      }
      
      // Check if profile is complete before allowing booking
      if (!this.profile.can_book || this.profile.profile_completion < 100) {
        this.showToast('Please complete your profile before booking. Missing: ' + (this.profile.missing_fields || []).join(', '), 'warning', 'Profile Incomplete', 5000);
        this.activeTab = 'profile';
        this.showProfileBanner = true;
        return;
      }
      this.showAddBookingModal = true;
      this.bookingForm.lotId = lot.id;
      this.fetchBookingData();
    },

    async fetchBookingData() {
      if (!this.bookingForm.lotId) return;

      try {
        this.bookingData = await userApi.getBookingData(this.bookingForm.lotId);
      } catch (err) {
        console.error('Error fetching booking data:', err);
        this.bookingData = {
          lot: {},
          vehicles: [],
          has_vehicles: false,
          has_active_reservation: false
        };
      }
    },

    // CRUD for Lots (Read only for user)
    async fetchLots() {
      try {
        const data = await userApi.getParkingLots();
        const mappedLots = data.map(lot => ({
          id: lot.id,
          name: lot.location,
          location: lot.address || lot.location,
          capacity: lot.total_spots,
          availableSpots: lot.available_spots || lot.total_spots,
          price: lot.price || 'N/A',
          pincode: lot.pincode,
          available_from: lot.available_from,
          available_to: lot.available_to,
          operatingHours: lot.available_from && lot.available_to
            ? `${lot.available_from} - ${lot.available_to}`
            : '24/7',
          isActive: lot.is_active !== false, // Active based on is_active field only
          isFavorite: false
        }));

        this.lots = mappedLots;
        this.allLots = [...mappedLots]; // Store copy for search

        // Load favorites after fetching lots
        this.loadFavorites();
      } catch (err) {
        console.error('Error fetching lots:', err);
        this.lots = [];
        this.allLots = [];
      }
    },

    // Profile Management
    async fetchProfile() {
      try {
        this.profile = await userApi.getProfile();
        console.log('Profile Data:', this.profile);
        console.log('Created At:', this.profile.created_at);
        this.profileLoaded = true;
        // Show banner only if profile is incomplete
        this.showProfileBanner = !this.profile.can_book || this.profile.profile_completion < 100;
      } catch (err) {
        console.error('Error fetching profile:', err);
        this.profileLoaded = true;
      }
    },

    // User Analytics
    async fetchUserAnalytics() {
      try {
        this.userAnalytics = await userApi.getAnalytics();
        console.log('User Analytics Data:', this.userAnalytics);
        console.log('Monthly Spending:', this.userAnalytics.monthly_spending);
      } catch (err) {
        console.error('Error fetching user analytics:', err);
        // Set default empty structure if fetch fails
        this.userAnalytics = {
          overview: {
            total_reservations: 0,
            total_spent: 0,
            completion_rate: 0,
            avg_rating_given: 0
          },
          monthly_spending: [],
          favorite_lots: [],
          weekly_activity: [],
          recent_activity: []
        };
      }
    },

    async updateProfile() {
      this.profileUpdating = true;
      this.profileError = "";
      this.profileSuccess = "";

      try {
        const updateData = {
          username: this.profile.username,
          first_name: this.profile.first_name,
          last_name: this.profile.last_name,
          phone_number: this.profile.phone_number,
          address: this.profile.address,
          pincode: this.profile.pincode,
          google_chat_webhook: this.profile.google_chat_webhook || null
        };

        // Add password fields if provided
        if (this.profileForm.current_password) {
          updateData.current_password = this.profileForm.current_password;
        }
        if (this.profileForm.new_password) {
          updateData.new_password = this.profileForm.new_password;
        }

        const data = await userApi.updateProfile(updateData);
        this.profileSuccess = data.message || 'Profile updated successfully!';
        this.profileForm.current_password = "";
        this.profileForm.new_password = "";

        // Refresh profile data to update completion status
        await this.fetchProfile();
        // Show banner again if profile is still incomplete
        if (!this.profile.can_book) {
          this.showProfileBanner = true;
        }

        // Close modal on success after a short delay to show success message
        setTimeout(() => {
          this.closeProfileEditModal();
        }, 1500);
      } catch (err) {
        console.error('Error updating profile:', err);
        this.profileError = err.message || 'Error updating profile. Please try again.';
      } finally {
        this.profileUpdating = false;
      }
    },

    // Delete Account
    async deleteAccount() {
      this.deleting = true;
      this.deleteError = "";

      try {
        const data = await userApi.deleteAccount({
          password: this.deleteForm.password,
          confirmation: this.deleteForm.confirmation
        });

        // Show success message
        this.showToast(data.message || 'Account deleted successfully. We\'re sorry to see you go!', 'success', 'Account Deleted', 3000);

        // Clear all local storage and session storage
        localStorage.clear();
        sessionStorage.clear();

        // Redirect to login page after a short delay
        setTimeout(() => {
          this.$router.push('/login');
        }, 1500);
      } catch (err) {
        console.error('Error deleting account:', err);
        this.deleteError = err.message || 'Error deleting account. Please try again.';
      } finally {
        this.deleting = false;
      }
    },

    closeDeleteModal() {
      this.showDeleteAccountModal = false;
      this.deleteForm = {
        password: "",
        confirmation: ""
      };
      this.deleteError = "";
    },

    // Favorites Management
    async toggleFavorite(lot) {
      try {
        if (lot.isFavorite) {
          // Remove from favorites
          await this.removeFavorite(lot.id);
          lot.isFavorite = false;
          this.favoriteLotIds = this.favoriteLotIds.filter(id => id !== lot.id);
          this.showToast('Removed from favorites', 'info', 'Favorites Updated');
        } else {
          // Add to favorites
          await this.addFavorite(lot.id);
          lot.isFavorite = true;
          this.favoriteLotIds.push(lot.id);
          this.showToast('Added to favorites', 'success', 'Favorites Updated');
        }
      } catch (err) {
        console.error('Error toggling favorite:', err);
        this.showToast('Error updating favorites. Please try again.', 'error', 'Favorites Error');
      }
    },

    async addFavorite(lotId) {
      try {
        await userApi.toggleFavorite(lotId, false); // false means add
      } catch (err) {
        console.error('Error adding favorite:', err);
        throw err;
      }
    },

    async removeFavorite(lotId) {
      try {
        await userApi.toggleFavorite(lotId, true); // true means remove
      } catch (err) {
        console.error('Error removing favorite:', err);
        throw err;
      }
    },

    async loadFavorites() {
      try {
        const favorites = await userApi.getFavorites();
        this.favoriteLotIds = favorites.map(fav => fav.id);

        // Update lots with favorite status
        this.lots.forEach(lot => {
          lot.isFavorite = this.favoriteLotIds.includes(lot.id);
        });
      } catch (err) {
        console.error('Error loading favorites:', err);
        this.favoriteLotIds = [];
      }
    },

    // Lot Details Modal Methods
    showLotDetails(lot) {
      this.selectedLot = lot;
      this.showLotDetailsModal = true;
    },

    closeLotDetailsModal() {
      this.showLotDetailsModal = false;
      this.selectedLot = null;
    },

    bookFromDetails() {
      if (this.selectedLot && this.selectedLot.id) {
        const lot = { ...this.selectedLot };  // Create a copy before closing modal
        this.closeLotDetailsModal();
        this.openBookModalForLot(lot);
      } else {
        this.showToast('Unable to book. Parking lot information is missing.', 'error', 'Error');
      }
    },

    toggleFavoriteFromDetails() {
      if (this.selectedLot) {
        this.toggleFavorite(this.selectedLot);
      }
    },

    getDisplayHours(lot) {
      // Check if both times are provided
      if (!lot.available_from || !lot.available_to || 
          lot.available_from === null || lot.available_to === null) {
        return '24/7';
      }

      // Convert to strings and trim whitespace
      const from = String(lot.available_from).toLowerCase().trim();
      const to = String(lot.available_to).toLowerCase().trim();

      // Check if it's truly 24/7 (various formats)
      const is24HourFrom = from === '00:00' || from === '00:00:00' || from === '12:00 am' || from === '0:00';
      const is24HourTo = to === '23:59' || to === '23:59:59' || to === '11:59 pm' || to === '24:00' || to === '24:00:00';

      if (is24HourFrom && is24HourTo) {
        return '24/7';
      }

      // Format the time display
      return `${lot.available_from} - ${lot.available_to}`;
    },

    // Profile Edit Modal Methods
    openProfileEditModal() {
      this.showProfileEditModal = true;
      // Clear any previous errors/success messages
      this.profileError = "";
      this.profileSuccess = "";
    },

    closeProfileEditModal() {
      this.showProfileEditModal = false;
      // Clear form data
      this.profileForm.current_password = "";
      this.profileForm.new_password = "";
      this.profileError = "";
      this.profileSuccess = "";
    },

    // Booking Details Modal Methods
    async showBookingDetails(booking) {
      // Fetch full booking details including rating, review, and payment status
      try {
        const [reservationResponse, paymentResponse] = await Promise.all([
          fetch(`http://localhost:5000/api/user/reservations/${booking.id}`, {
            headers: { 'auth-token': localStorage.getItem('auth-token') }
          }),
          fetch(`http://localhost:5000/api/user/payments/${booking.id}`, {
            headers: { 'auth-token': localStorage.getItem('auth-token') }
          })
        ]);
        
        if (reservationResponse.ok) {
          const data = await reservationResponse.json();
          const reservation = data.reservation || data;
          
          // Get payment status
          let paymentStatus = 'unpaid';
          if (paymentResponse.ok) {
            const paymentData = await paymentResponse.json();
            paymentStatus = paymentData.payment_exists ? 'paid' : 'unpaid';
          }
          
          // Get vehicle and lot details
          const [vehicles, lots] = await Promise.all([
            userApi.getVehicles(),
            userApi.getParkingLots()
          ]);
          
          const vehicle = vehicles.find(v => v.id === reservation.vehicle_id);
          const lot = lots.find(l => l.id === reservation.lot_id);
          
          this.selectedBooking = {
            id: reservation.id,
            bookingId: reservation.booking_id || `BOOK-${reservation.id}`,
            lotName: lot?.location || booking.lotName || 'Unknown Location',
            lotId: reservation.lot_id || booking.lot_id,
            spotNumber: reservation.spot && reservation.spot.spot_number ? `Spot #${reservation.spot.spot_number}` : (reservation.spot_id ? `Spot #${reservation.spot_id}` : 'N/A'),
            vehicleNumber: vehicle?.vehicle_number || booking.vehicleNumber || 'Unknown',
            cost: reservation.cost || booking.cost || 0,
            scheduledTime: reservation.expected_arrival ? this.formatDateTime(reservation.expected_arrival) : booking.scheduledTime || 'N/A',
            checkInTime: reservation.start ? this.formatDateTime(reservation.start) : 'Not Parked Yet',
            checkOutTime: reservation.end ? this.formatDateTime(reservation.end) : 'Not Left Yet',
            status: reservation.status || booking.status || 'Unknown',
            rating: reservation.rating ? '★'.repeat(reservation.rating) : null,
            ratingValue: reservation.rating || null,
            review: reservation.review || null,
            paymentStatus: paymentStatus
          };
        } else {
          // Fallback to booking data if API call fails
          this.selectedBooking = {
            ...booking,
            ratingValue: booking.rating ? booking.rating.length : null,
            paymentStatus: 'unpaid',
            review: null
          };
        }
      } catch (err) {
        console.error('Error fetching booking details:', err);
        // Fallback to booking data
        this.selectedBooking = {
          ...booking,
          ratingValue: booking.rating ? booking.rating.length : null,
          review: null
        };
      }
      
      this.showBookingDetailsModal = true;
    },

    async showHistoryDetails(history) {
      // Use the same logic as showBookingDetails to ensure consistency
      await this.showBookingDetails(history);
    },

    closeBookingDetailsModal() {
      this.showBookingDetailsModal = false;
      this.selectedBooking = null;
    },

    makePayment(booking) {
      // Close booking details modal
      this.closeBookingDetailsModal();
      
      // Open payment modal with booking details
      this.paymentData = {
        reservationId: booking.id,
        bookingId: booking.bookingId,
        amount: parseFloat(booking.cost) || 0,
        durationHours: 0 // Will be calculated from booking data if needed
      };
      
      this.showPaymentModal = true;
    },

    leaveReview(booking) {
      // Close booking details modal
      this.closeBookingDetailsModal();
      
      // Open review modal with booking details
      const reservation = {
        id: booking.id,
        lotId: booking.lotId,
        lotName: booking.lotName
      };
      
      this.openReviewModal(reservation);
    },

    async cancelBooking(bookingId) {
      if (!confirm('Are you sure you want to cancel this booking?')) return;
      
      try {
        const response = await fetch(`http://localhost:5000/api/user/cancel_booking/${bookingId}`, {
          method: 'POST',
          headers: {
            'auth-token': localStorage.getItem('auth-token')
          }
        });
        
        if (response.ok) {
          this.showToast('Booking cancelled successfully', 'success', 'Booking Cancelled');
          this.closeBookingDetailsModal();
          this.fetchBookings();
          this.fetchHomeData();
        } else {
          const data = await response.json();
          this.showToast('Failed to cancel booking: ' + (data.error || 'Unknown error'), 'error', 'Cancellation Failed');
        }
      } catch (err) {
        console.error('Error cancelling booking:', err);
        this.showToast('Failed to cancel booking. Please try again.', 'error', 'Cancellation Failed');
      }
    },

    async downloadBooking(booking) {
      // For PDF generation, we'll use jsPDF library
      // First check if jsPDF is available, if not, use a simple approach
      try {
        // Create a printable HTML content
        const printWindow = window.open('', '', 'height=600,width=800');
        printWindow.document.write(`
          <html>
            <head>
              <title>Booking Receipt - ${booking.bookingId}</title>
              <style>
                body { font-family: Arial, sans-serif; padding: 40px; }
                .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 20px; }
                .header h1 { margin: 0; color: #1976d2; }
                .header p { margin: 5px 0; color: #666; }
                .content { margin: 20px 0; }
                .row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #eee; }
                .label { font-weight: 600; color: #666; }
                .value { color: #333; }
                .footer { margin-top: 40px; text-align: center; color: #999; font-size: 12px; }
                @media print { button { display: none; } }
              </style>
            </head>
            <body>
              <div class="header">
                <h1>PARKEASE</h1>
                <p>Booking Receipt</p>
              </div>
              <div class="content">
                <div class="row">
                  <span class="label">Booking ID:</span>
                  <span class="value">${booking.bookingId}</span>
                </div>
                <div class="row">
                  <span class="label">Parking Lot:</span>
                  <span class="value">${booking.lotName}</span>
                </div>
                <div class="row">
                  <span class="label">Spot Number:</span>
                  <span class="value">${booking.spotNumber}</span>
                </div>
                <div class="row">
                  <span class="label">Vehicle:</span>
                  <span class="value">${booking.vehicleNumber}</span>
                </div>
                <div class="row">
                  <span class="label">Scheduled Time:</span>
                  <span class="value">${booking.scheduledTime}</span>
                </div>
                <div class="row">
                  <span class="label">Status:</span>
                  <span class="value">${booking.status}</span>
                </div>
                <div class="row">
                  <span class="label">Cost:</span>
                  <span class="value">₹${booking.cost}</span>
                </div>
              </div>
              <div class="footer">
                <p>Thank you for using ParkEase!</p>
                <p>Generated on ${new Date().toLocaleString()}</p>
              </div>
              <div style="text-align: center; margin-top: 20px;">
                <button onclick="window.print()" style="padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                  Print / Save as PDF
                </button>
              </div>
            </body>
          </html>
        `);
        printWindow.document.close();
      } catch (err) {
        console.error('Error generating receipt:', err);
        alert('Failed to generate receipt. Please try again.');
      }
    },

    rebookParking(booking) {
      this.closeBookingDetailsModal();
      this.bookingForm.lotId = booking.lot_id || '';
      this.bookingForm.vehicle_id = booking.vehicle_id || '';
      this.openBookingModal();
    },

    formatTime(dateTimeStr) {
      if (!dateTimeStr) return 'N/A';
      const date = new Date(dateTimeStr);
      return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    },

    // Utility method for date formatting
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    },

    logout() {
      localStorage.removeItem('auth-token');
      this.$router.push('/login');
    },

    // User Analytics Methods
    async fetchUserAnalytics() {
      try {
        this.userAnalytics = await userApi.getAnalytics();
      } catch (err) {
        console.error('Error fetching user analytics:', err);
      }
    },

    // Redirect to profile tab to add vehicle
    redirectToVehicles() {
      this.closeBookingModal();
      this.activeTab = 'profile';
      alert('Please add a vehicle from your profile page before booking parking.');
      // Scroll to vehicles section after a short delay
      setTimeout(() => {
        const vehiclesSection = document.querySelector('.vehicles-section');
        if (vehiclesSection) {
          vehiclesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 300);
      this.closeBookingModal();
    },

    completeProfileClick() {
      this.activeTab = 'profile';
      this.showProfileBanner = false;
      // Open the profile edit modal directly
      setTimeout(() => {
        this.openProfileEditModal();
      }, 100);
    },

    // Export CSV
    async exportCSV() {
      this.taskLoading = true;
      this.taskError = null;
      
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/user/export', {
          method: 'POST',
          headers: {
            'auth-token': token,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          this.$refs.toast.show(
            `Parking history export started. You will receive an email at ${data.user_email} when the CSV is ready.`,
            'success',
            'Export Started'
          );
        } else {
          const errorData = await response.json();
          this.taskError = errorData.error || 'Failed to start export';
          this.$refs.toast.show('Failed to start export', 'error');
        }
      } catch (err) {
        this.taskError = err.message || 'Failed to export CSV';
        this.$refs.toast.show('Failed to export CSV', 'error');
      } finally {
        this.taskLoading = false;
      }
    },

    // Search functionality
    handleSearch() {
      if (!this.searchQuery.trim()) {
        this.lots = [...this.allLots];
        return;
      }

      const query = this.searchQuery.toLowerCase();
      this.lots = this.allLots.filter(lot => 
        lot.name.toLowerCase().includes(query) ||
        lot.location.toLowerCase().includes(query) ||
        (lot.pincode && lot.pincode.toString().includes(query))
      );
    },

    clearSearch() {
      this.searchQuery = '';
      this.lots = [...this.allLots];
    },

    // Toast notification helper
    showToast(message, type = 'info', title = '') {
      if (this.$refs.toast) {
        this.$refs.toast.show(message, type, title);
      }
    },

    handleToastEvent(event) {
      const { message, type, title } = event.detail;
      this.showToast(message, type, title);
    }
  },

  async mounted() {
    // Fetch initial data
    await Promise.all([
      this.fetchProfile(),
      this.fetchBookings(),
      this.fetchLots(),
      this.vehicleCrud.fetchItems(),
      this.fetchUserAnalytics(),
      this.fetchHomeData()
    ]);

    // Set up live duration timer for currently parked vehicle
    this.durationTimer = setInterval(() => {
      this.currentTime = new Date();
    }, 60000); // Update every minute

    // Listen for profile refresh events
    window.addEventListener('refreshProfile', this.handleProfileRefresh);
    
    // Listen for toast events
    window.addEventListener('showToast', this.handleToastEvent);
  },

  beforeUnmount() {
    // Clean up timer
    if (this.durationTimer) {
      clearInterval(this.durationTimer);
    }
    // Remove event listeners
    window.removeEventListener('refreshProfile', this.handleProfileRefresh);
    window.removeEventListener('showToast', this.handleToastEvent);
  }
};
</script>

<style scoped>
@import '@/assets/styles/UserDashboard.css';

/* Form label and required field styling */
label {
  display: block;
  margin-bottom: 1rem;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

label .required {
  color: #dc3545;
  margin-left: 0.25rem;
  font-weight: bold;
  display: inline !important;
  vertical-align: baseline;
}

/* Form input and select styling */
label input,
label select,
label textarea {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  margin-top: 0.25rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s ease;
}

label input:focus,
label select:focus,
label textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

label select {
  cursor: pointer;
  background-color: white;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23333' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  padding-right: 2.5rem;
}

label small {
  display: block;
  margin-top: 0.25rem;
  font-size: 12px;
  color: #6c757d;
  font-weight: normal;
}

/* Lot Details Modal - Sober & Aesthetic Styling */
.lot-details-modal {
  padding: 0;
}

.lot-header-section {
  padding: 1.5rem 0 1rem 0;
  border-bottom: 1px solid #e8e8e8;
  margin-bottom: 1.5rem;
}

.lot-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.lot-modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.lot-details-modal .status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
  background: #f0f0f0;
  color: #666;
}

.lot-details-modal .status-badge.active {
  background: #e8f5e9;
  color: #2e7d32;
}

.lot-details-modal .status-badge.inactive {
  background: #ffebee;
  color: #c62828;
}

.lot-details-modal .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.lot-location {
  color: #666;
  font-size: 0.95rem;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.lot-location i {
  color: #999;
  font-size: 0.9rem;
}

.lot-info-sections {
  display: flex;
  flex-direction: column;
  gap: 1.3rem;
}

.info-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.info-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.info-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 8px;
  color: #667eea;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.info-content h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.8rem;
  font-weight: 500;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-content p {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}

.capacity-section {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.capacity-section h4 {
  margin: 0 0 1rem 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.capacity-section h4 i {
  color: #667eea;
  font-size: 0.9rem;
}

.capacity-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.capacity-numbers {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.capacity-numbers .available {
  color: #2e7d32;
  font-weight: 600;
}

.capacity-numbers .total {
  color: #666;
  font-weight: 500;
}

.capacity-bar {
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.capacity-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.occupancy-text {
  font-size: 0.8rem;
  color: #666;
  text-align: center;
  display: block;
}

.features-section {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.features-section h4 {
  margin: 0 0 1rem 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.features-section h4 i {
  color: #667eea;
  font-size: 0.9rem;
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #555;
}

.feature-item i {
  color: #667eea;
  font-size: 1rem;
  width: 20px;
  text-align: center;
}

.lot-details-modal .modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e8e8e8;
}

.book-from-details-btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.book-from-details-btn:hover {
  background: #5568d3;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.favorite-from-details-btn {
  padding: 0.75rem 1rem;
  background: white;
  color: #666;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.favorite-from-details-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.favorite-from-details-btn.favorited {
  color: #e91e63;
  border-color: #e91e63;
  background: #fce4ec;
}

.close-details-btn {
  padding: 0.75rem 1.5rem;
  background: white;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-details-btn:hover {
  background: #f5f5f5;
  border-color: #bbb;
}

/* Notification Preferences Styling */
.section-description {
  color: #666;
  font-size: 0.9rem;
  margin: 0.25rem 0 0.75rem 0;
}

.notification-option {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  margin-bottom: 0.5rem;
}

.option-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.option-header i {
  color: #667eea;
  font-size: 1.1rem;
}

.option-title {
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
}

.badge-enabled {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.help-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.help-link:hover {
  text-decoration: underline;
}

.webhook-help {
  margin-top: 0.75rem;
  padding: 1rem;
  background: white;
  border-left: 3px solid #667eea;
  border-radius: 4px;
  font-size: 0.85rem;
}

.webhook-help p {
  margin: 0 0 0.5rem 0;
  font-weight: 600;
  color: #2c3e50;
}

.webhook-help ol {
  margin: 0.5rem 0 0 1.25rem;
  padding: 0;
}

.webhook-help li {
  margin: 0.35rem 0;
  color: #555;
}

.webhook-help a {
  color: #667eea;
  text-decoration: none;
}

.webhook-help a:hover {
  text-decoration: underline;
}

.form-divider {
  height: 1px;
  background: #e0e0e0;
  margin: 1rem 0 0.75rem 0;
}

.redirect-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  margin-top: 10px;
  transition: background-color 0.3s ease;
}

.redirect-btn:hover {
  background: #0056b3;
}

.redirect-btn:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}
</style>