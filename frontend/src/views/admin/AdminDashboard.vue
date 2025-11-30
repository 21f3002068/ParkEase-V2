<template>
  <div class="admin-dashboard">
    <!-- Sidebar -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2><i class="fas fa-parking"></i> ParkEase</h2>
        <p class="user-role">Admin Panel</p>
      </div>
      
      <nav class="sidebar-nav">
        <button 
          @click="activeTab = 'lots'" 
          :class="{ 'active': activeTab === 'lots' }"
          class="nav-item"
        >
          <span class="nav-icon"><i class="fas fa-building"></i></span>
          <span class="nav-text">Parking Lots</span>
        </button>
        <button 
          @click="activeTab = 'visualization'" 
          :class="{ 'active': activeTab === 'visualization' }"
          class="nav-item"
        >
          <span class="nav-icon"><i class="fas fa-eye"></i></span>
          <span class="nav-text">Bird's Eye</span>
        </button>
        <button 
          @click="activeTab = 'users'" 
          :class="{ 'active': activeTab === 'users' }"
          class="nav-item"
        >
          <span class="nav-icon"><i class="fas fa-users"></i></span>
          <span class="nav-text">Users</span>
        </button>
        <button 
          @click="activeTab = 'reservations'" 
          :class="{ 'active': activeTab === 'reservations' }"
          class="nav-item"
        >
          <span class="nav-icon"><i class="fas fa-calendar-check"></i></span>
          <span class="nav-text">Reservations</span>
        </button>
        <button 
          @click="activeTab = 'analytics'" 
          :class="{ 'active': activeTab === 'analytics' }"
          class="nav-item"
        >
          <span class="nav-icon"><i class="fas fa-chart-line"></i></span>
          <span class="nav-text">Summaries</span>
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
        </div>
        <div class="header-right">
          <button 
            @click="showTaskLogs = !showTaskLogs" 
            class="task-logs-header-btn"
            title="View Task Logs"
          >
            <i class="fas fa-history"></i>
            <span>Task Logs</span>
            <span class="logs-count">{{ taskLogs.length }}</span>
          </button>
        </div>
      </div>
      
      <!-- Task Logs Dropdown (Global) -->
      <div v-if="showTaskLogs" class="task-logs-dropdown-global">
        <div v-if="taskLogs.length === 0" class="no-logs">
          No task logs yet. Run a task to see logs here.
        </div>
        <div v-else class="task-log-list">
          <div v-for="log in taskLogs.slice(0, 10)" :key="log.id" :class="['task-log-item', `log-${log.status}`]">
            <div class="log-header">
              <span class="log-task">{{ log.taskName }}</span>
              <span class="log-time">{{ log.timestamp }}</span>
            </div>
            <div class="log-message">{{ log.message }}</div>
          </div>
        </div>
      </div>

      <!-- Overview Cards - Visible on main tabs only (not on visualization or tasks) -->
      <div v-if="activeTab !== 'visualization' && activeTab !== 'tasks'" class="analytics-overview">
        <div class="stat-card">
          <h3>{{ analytics.overview?.total_users || 0 }}</h3>
          <p>Total Users</p>
        </div>
        <div class="stat-card">
          <h3>{{ analytics.overview?.total_lots || 0 }}</h3>
          <p>Total Parking Lots</p>
        </div>
        <div class="stat-card">
          <h3>{{ analytics.overview?.total_spots || 0 }}</h3>
          <p>Total Parking Spots</p>
        </div>
        <div class="stat-card">
          <h3>{{ analytics.overview?.occupancy_rate || 0 }}%</h3>
          <p>Current Occupancy</p>
        </div>
        <div class="stat-card">
          <h3>₹{{ formatInteger(analytics.overview?.net_earnings) }}</h3>
          <p>Net Earnings</p>
        </div>
      </div>

    <div v-if="activeTab === 'lots'" class="tab-content">
      <div class="lots-header">
        <div class="header-actions">
          <div class="search-bar">
            <i class="fas fa-search"></i>
            <input 
              v-model="lotsSearchQuery" 
              type="text" 
              placeholder="Search lots by name, location, or pincode..."
              @input="filterLots"
            />
            <button v-if="lotsSearchQuery" @click="clearLotsSearch" class="clear-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <button @click="showAddLotModal = true" class="add-lot-btn">
            <i class="fas fa-plus"></i>
            <span>Add Lot</span>
          </button>
        </div>
      </div>
      
      <div v-if="lotsLoading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading lots...
      </div>
      
      <div v-if="lotsError" class="error">{{ lotsError }}</div>
      
      <!-- Parking Lots Cards Grid -->
      <div v-if="!lotsLoading && filteredLots.length" class="lots-grid">
        <!-- Existing Parking Lot Cards -->
        <div v-for="lot in filteredLots" :key="lot.id" class="lot-card" :class="{ 'inactive-lot-card': !lot.is_active }">
          <div class="lot-card-header">
            <h3>{{ lot.name }}</h3>
          </div>

          <div class="lot-card-body">
            <div class="lot-info">
              <div class="info-item">
                <i class="fas fa-map-marker-alt"></i>
                <span>{{ lot.location }}</span>
              </div>
              <div class="info-item">
                <i class="fas fa-map-pin"></i>
                <span>{{ lot.pincode }}</span>
              </div>
              <div class="info-item">
                <i class="fas fa-car"></i>
                <span>{{ lot.available_spots }}/{{ lot.capacity }} available</span>
              </div>
              <div class="info-item">
                <i class="fas fa-rupee-sign"></i>
                <span>₹{{ formatInteger(lot.price) }}/hour</span>
              </div>
              <div class="info-item" v-if="lot.available_from && lot.available_to">
                <i class="fas fa-clock"></i>
                <span>{{ lot.available_from }} - {{ lot.available_to }}</span>
              </div>
              <div class="info-item">
                <i class="fas fa-chart-pie"></i>
                <span>
                  {{ Math.round((lot.occupied_spots / lot.capacity) * 100) }}% occupied
                  <div class="occupancy-bar">
                    <div 
                      class="occupancy-fill" 
                      :style="{ width: Math.round((lot.occupied_spots / lot.capacity) * 100) + '%' }"
                      :class="{
                        'low': Math.round((lot.occupied_spots / lot.capacity) * 100) < 50,
                        'medium': Math.round((lot.occupied_spots / lot.capacity) * 100) >= 50 && Math.round((lot.occupied_spots / lot.capacity) * 100) < 80,
                        'high': Math.round((lot.occupied_spots / lot.capacity) * 100) >= 80
                      }"
                    ></div>
                  </div>
                </span>
              </div>
            </div>
          </div>

          <!-- Three Dots Menu in Top Right -->
          <div class="lot-card-menu">
            <button 
              class="menu-trigger"
              @click.stop="toggleMenu(lot.id)"
            >
              <i class="fas fa-ellipsis-v"></i>
            </button>
            <div 
              v-if="activeMenu === lot.id" 
              class="menu-dropdown"
              @click.stop
            >
              <button 
                @click="editLot(lot); activeMenu = null" 
                class="menu-item"
              >
                <i class="fas fa-edit"></i>
                <span>Edit</span>
              </button>
              <button 
                @click="deleteLot(lot.id); activeMenu = null" 
                class="menu-item delete"
              >
                <i class="fas fa-trash"></i>
                <span>Delete</span>
              </button>
              <button 
                @click="toggleLotStatus(lot); activeMenu = null" 
                class="menu-item"
              >
                <i :class="lot.is_active ? 'fas fa-toggle-off' : 'fas fa-toggle-on'"></i>
                <span>{{ lot.is_active ? 'Deactivate' : 'Activate' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else-if="!lotsLoading && lotsSearchQuery && !filteredLots.length" class="empty-state">
        <i class="fas fa-search"></i>
        <h3>No results found</h3>
        <p>No parking lots match your search criteria</p>
        <button @click="clearLotsSearch" class="add-btn">
          <i class="fas fa-times"></i> Clear Search
        </button>
      </div>
      
      <div v-else-if="!lotsLoading && !lots.length" class="empty-state">
        <i class="fas fa-parking"></i>
        <h3>No parking lots found</h3>
        <p>Get started by adding your first parking lot</p>
        <button @click="showAddLotModal = true" class="add-btn">
          <i class="fas fa-plus"></i> Add Parking Lot
        </button>
      </div>
    </div>

    <div v-if="activeTab === 'users'" class="tab-content">
      <div class="users-header">
        <div class="users-actions">
          <div class="search-bar">
            <i class="fas fa-search"></i>
            <input 
              v-model="usersSearchQuery" 
              type="text" 
              placeholder="Search users by name, email, or username..."
              @input="filterUsers"
            />
            <button v-if="usersSearchQuery" @click="clearUsersSearch" class="clear-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <button @click="exportUsersCSV" :disabled="usersExportLoading" class="export-users-btn">
            <i class="fas fa-file-csv"></i>
            <span>{{ usersExportLoading ? 'Exporting...' : 'Export Users CSV' }}</span>
          </button>
          <button @click="openFlaggedUsersModal" class="view-flagged-btn">
            <i class="fas fa-flag"></i>
            <span>View Flagged Users</span>
          </button>
          <button @click="showAddUserModal = true" class="add-user-btn">
            <i class="fas fa-user-plus"></i>
            <span>Add User</span>
          </button>
        </div>
      </div>
      
      <div class="users-table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Username</th>
              <!-- Status column removed per latest UX request -->
              <th>Roles</th>
              <th>Joined</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredUsers.length === 0">
              <td colspan="6" class="no-results">
                <i class="fas fa-search"></i>
                <p>No users match your search criteria</p>
              </td>
            </tr>
            <tr v-for="user in filteredUsers" :key="user.id" :class="{ 'inactive-user': !user.active }">
              <td>
                <button @click="showUserDetails(user)" class="user-id-link">
                  #{{ user.id }}
                </button>
              </td>
              <td class="user-name">
                <div class="name-display">{{ user.first_name }} {{ user.last_name }}</div>
              </td>
              <td class="user-email">{{ user.email }}</td>
              <td class="username">{{ user.username }}</td>
              <td class="user-roles">
                <div class="roles-container">
                  <span v-for="role in user.roles" :key="role" class="role-badge">
                    {{ role }}
                  </span>
                </div>
              </td>
              <td class="join-date">{{ formatDate(user.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Top Users Section -->
      <div class="top-users-section">
        <h3><i class="fas fa-trophy"></i> Top Users (Last 30 Days)</h3>
        <table class="top-users-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Total Bookings</th>
              <th>Total Spent</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in analytics.top_users" :key="user.email">
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.total_bookings }}</td>
              <td>₹{{ formatInteger(user.total_spent) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- User Detail Modal -->
      <div v-if="showUserDetailModal" class="modal-overlay">
        <div class="modal user-detail-modal">
          <div class="modal-header">
            <h3><i class="fas fa-user"></i> User Details</h3>
            <button class="close-button" @click="closeUserDetailModal">×</button>
          </div>
          
          <div class="modal-content" v-if="selectedUser">
            <div v-if="userDetailsLoading" class="loading-state">
              <i class="fas fa-spinner fa-spin"></i> Loading user details...
            </div>
            
            <div v-else>
              <div class="user-detail-info">
                <div class="user-avatar">
                  <i class="fas fa-user-circle"></i>
                </div>
                
                <div class="user-basic-info">
                  <h4>{{ userDetails.user?.first_name }} {{ userDetails.user?.last_name }}</h4>
                  <p class="user-email">{{ userDetails.user?.email }}</p>
                  <p class="user-username">@{{ userDetails.user?.username }}</p>
                  <div class="status-badges">
                    <span :class="['status-badge', userDetails.user?.active ? 'status-active' : 'status-inactive']">
                      <i :class="userDetails.user?.active ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
                      {{ userDetails.user?.active ? 'Active' : 'Inactive' }}
                    </span>
                    <span v-if="userDetails.user?.is_flagged" class="status-badge status-flagged">
                      <i class="fas fa-flag"></i>
                      Flagged
                    </span>
                  </div>
                </div>
              </div>
              
              <div class="user-details-tabs">
                <button 
                  @click="activeUserTab = 'info'" 
                  :class="['tab-btn', { 'active': activeUserTab === 'info' }]"
                >
                  <i class="fas fa-info-circle"></i> Basic Info
                </button>
                <button 
                  @click="activeUserTab = 'vehicles'" 
                  :class="['tab-btn', { 'active': activeUserTab === 'vehicles' }]"
                >
                  <i class="fas fa-car"></i> Vehicles ({{ userDetails.vehicles?.length || 0 }})
                </button>
                <button 
                  @click="activeUserTab = 'reservations'" 
                  :class="['tab-btn', { 'active': activeUserTab === 'reservations' }]"
                >
                  <i class="fas fa-calendar-check"></i> Reservations ({{ userDetails.reservations?.length || 0 }})
                </button>
              </div>
              
              <!-- Basic Info Tab -->
              <div v-if="activeUserTab === 'info'" class="tab-content-detail">
                <div class="user-details-grid">
                  <div class="detail-item">
                    <label>User ID</label>
                    <span>#{{ userDetails.user?.id }}</span>
                  </div>
                  <div class="detail-item">
                    <label>Member Since</label>
                    <span>{{ formatDate(userDetails.user?.created_at) }}</span>
                  </div>
                  <div class="detail-item">
                    <label>Phone Number</label>
                    <span>{{ userDetails.user?.phone_number || 'Not provided' }}</span>
                  </div>
                  <div class="detail-item">
                    <label>Address</label>
                    <span>{{ userDetails.user?.address || 'Not provided' }}</span>
                  </div>
                  <div class="detail-item">
                    <label>PIN Code</label>
                    <span>{{ userDetails.user?.pincode || 'Not provided' }}</span>
                  </div>
                  <div class="detail-item">
                    <label>Roles</label>
                    <div class="roles-container">
                      <span v-for="role in userDetails.user?.roles" :key="role.name" class="role-badge">
                        {{ role.name }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Vehicles Tab -->
              <div v-if="activeUserTab === 'vehicles'" class="tab-content-detail">
                <div v-if="userDetails.vehicles?.length === 0" class="empty-state-small">
                  <i class="fas fa-car"></i>
                  <p>No vehicles registered</p>
                </div>
                <div v-else class="vehicles-list">
                  <div v-for="vehicle in userDetails.vehicles" :key="vehicle.id" class="vehicle-item">
                    <div class="vehicle-info">
                      <div class="license-plate">{{ vehicle.license_plate }}</div>
                      <div class="vehicle-model">{{ vehicle.model }}</div>
                      <div v-if="vehicle.color" class="vehicle-color">{{ vehicle.color }}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Reservations Tab -->
              <div v-if="activeUserTab === 'reservations'" class="tab-content-detail">
                <div v-if="userDetails.reservations?.length === 0" class="empty-state-small">
                  <i class="fas fa-calendar-times"></i>
                  <p>No reservations found</p>
                </div>
                <div v-else class="reservations-list">
                  <div v-for="reservation in userDetails.reservations" :key="reservation.id" class="reservation-item">
                    <div class="reservation-header">
                      <span class="reservation-id">#{{ reservation.id }}</span>
                      <span :class="['status-badge', 'status-' + reservation.status.toLowerCase().replace(' ', '-')]">
                        {{ reservation.status }}
                      </span>
                    </div>
                    <div class="reservation-details">
                      <div class="detail-row">
                        <i class="fas fa-building"></i>
                        <span>{{ reservation.parking_lot }}</span>
                      </div>
                      <div class="detail-row">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>Spot {{ reservation.spot_number }}</span>
                      </div>
                      <div class="detail-row">
                        <i class="fas fa-calendar"></i>
                        <span>{{ formatDateTime(reservation.booking_timestamp) }}</span>
                      </div>
                      <div v-if="reservation.parking_cost" class="detail-row">
                        <i class="fas fa-rupee-sign"></i>
                        <span>₹{{ formatInteger(reservation.parking_cost) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="user-actions">
                <button 
                  @click="toggleUserFlag(userDetails.user?.id)" 
                  :class="['action-btn', userDetails.user?.is_flagged ? 'unflag-btn' : 'flag-btn']"
                >
                  <i :class="userDetails.user?.is_flagged ? 'fas fa-flag-checkered' : 'fas fa-flag'"></i>
                  {{ userDetails.user?.is_flagged ? 'Unflag User' : 'Flag User' }}
                </button>
                <button 
                  @click="toggleUserActive(userDetails.user?.id)" 
                  :class="['action-btn', userDetails.user?.active ? 'deactivate-btn' : 'activate-btn']"
                >
                  <i :class="userDetails.user?.active ? 'fas fa-user-slash' : 'fas fa-user-check'"></i>
                  {{ userDetails.user?.active ? 'Deactivate' : 'Activate' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Flagged Users Modal -->
      <div v-if="showFlaggedUsersModal" class="modal-overlay">
        <div class="modal flagged-users-modal">
          <div class="modal-header">
            <h3><i class="fas fa-flag"></i> Flagged Users</h3>
            <button class="close-button" @click="closeFlaggedUsersModal">×</button>
          </div>
          
          <div class="modal-content">
            <div v-if="flaggedUsersLoading" class="loading-state">
              <i class="fas fa-spinner fa-spin"></i> Loading flagged users...
            </div>
            
            <div v-else-if="flaggedUsers.length === 0" class="empty-state">
              <i class="fas fa-flag"></i>
              <h4>No Flagged Users</h4>
              <p>No users have been flagged yet.</p>
            </div>
            
            <div v-else class="flagged-users-table-container">
              <table class="flagged-users-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="user in flaggedUsers" :key="user.id" :class="{ 'inactive-user': !user.active }">
                    <td>
                      <button @click="showUserDetails(user)" class="user-id-link">
                        #{{ user.id }}
                      </button>
                    </td>
                    <td class="user-name">{{ user.first_name }} {{ user.last_name }}</td>
                    <td class="user-email">{{ user.email }}</td>
                    <td class="user-status">
                      <span :class="['status-badge', user.active ? 'status-active' : 'status-inactive']">
                        <i :class="user.active ? 'fas fa-check-circle' : 'fas fa-times-circle'"></i>
                        {{ user.active ? 'Active' : 'Inactive' }}
                      </span>
                    </td>
                    <td class="actions">
                      <button @click="unflagUser(user.id)" class="action-btn unflag-btn" title="Unflag user">
                        <i class="fas fa-flag-checkered"></i>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Add/Edit User Modal -->
      <div v-if="showAddUserModal || showEditUserModal" class="modal-overlay">
        <div class="modal">
          <h3>{{ showEditUserModal ? 'Edit' : 'Add' }} User</h3>
          <form @submit.prevent="showEditUserModal ? updateUser() : addUser()">
            <label>
              Email:
              <input v-model="userForm.email" type="email" required />
            </label>
            <label>
              Username:
              <input v-model="userForm.username" required />
            </label>
            <label v-if="!showEditUserModal">
              Password:
              <input v-model="userForm.password" type="password" required />
            </label>
            <label>
              Roles (comma separated):
              <input v-model="userForm.roles" required />
            </label>
            <div class="modal-actions">
              <button type="submit">{{ showEditUserModal ? 'Update' : 'Add' }}</button>
              <button type="button" @click="closeUserModal">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Reservations Tab -->
    <div v-if="activeTab === 'reservations'" class="tab-content">
      <div class="reservations-header">
        <div class="reservations-filters">
          <select v-model="reservationFilter" @change="fetchReservations" class="filter-select">
            <option value="all">All Reservations</option>
            <option value="active">Active Only</option>
            <option value="completed">Completed Only</option>
          </select>
        </div>
        <div class="reservations-actions">
          <button @click="exportReservationsCSV" :disabled="reservationsExportLoading" class="export-btn">
            <i class="fas fa-file-export"></i>
            {{ reservationsExportLoading ? 'Exporting…' : 'Export Reservations CSV' }}
          </button>
        </div>
      </div>
      
      <div v-if="reservationsLoading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading reservations...
      </div>
      
      <div v-if="reservationsError" class="error">{{ reservationsError }}</div>
      
      <div v-if="!reservationsLoading && reservations.length" class="reservations-table-container">
        <table class="reservations-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>User</th>
              <th>Parking Lot</th>
              <th>Spot</th>
              <th>Vehicle</th>
              <th>Check-in</th>
              <th>Check-out</th>
              <th>Duration</th>
              <th>Cost</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="reservation in reservations" :key="reservation.id" :class="{ 'active-reservation': reservation.status === 'Active' }">
              <td class="reservation-id">
                <button @click="showReservationDetails(reservation)" class="id-link">
                  #{{ reservation.id }}
                </button>
              </td>
              <td class="user-info">
                <div class="user-name">{{ reservation.user.first_name }} {{ reservation.user.last_name }}</div>
                <div class="user-email">{{ reservation.user.email }}</div>
              </td>
              <td class="lot-info">
                <div class="lot-name">{{ reservation.parking_lot.name }}</div>
                <div class="lot-address">{{ reservation.parking_lot.address }}</div>
              </td>
              <td class="spot-number">{{ reservation.spot.spot_number }}</td>
              <td class="vehicle-info">
                <div v-if="reservation.vehicle" class="vehicle-card">
                  <div class="vehicle-icon"><i class="fas fa-car-side"></i></div>
                  <div class="vehicle-copy">
                    <div class="license-plate">{{ reservation.vehicle.license_plate }}</div>
                    <div class="vehicle-model">{{ reservation.vehicle.model }}</div>
                  </div>
                </div>
                <div v-else class="no-vehicle">No vehicle info</div>
              </td>
              <td class="timestamp-cell">
                <div class="time-chip time-chip--checkin">
                  {{ reservation.parking_timestamp ? formatTimeOnly(reservation.parking_timestamp) : '--:--' }}
                </div>
                <small class="date-subtext">
                  {{ reservation.parking_timestamp ? formatDateOnly(reservation.parking_timestamp) : 'Not checked-in yet' }}
                </small>
              </td>
              <td class="timestamp-cell">
                <div :class="['time-chip', 'time-chip--checkout', { 'time-chip--empty': !reservation.leaving_timestamp }]">
                  {{ reservation.leaving_timestamp ? formatTimeOnly(reservation.leaving_timestamp) : '--:--' }}
                </div>
                <small class="date-subtext">
                  {{ reservation.leaving_timestamp ? formatDateOnly(reservation.leaving_timestamp) : 'Not checked out yet' }}
                </small>
              </td>
              <td class="duration">{{ formatDuration(reservation) }}</td>
              <td class="cost">₹{{ formatInteger(reservation.parking_cost) }}</td>
              <td class="status">
                <span :class="['status-badge', 'status-' + reservation.status.toLowerCase().replace(' ', '-')]">
                  {{ reservation.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        
        <!-- Pagination -->
        <div v-if="reservationsPagination.pages > 1" class="pagination">
          <div class="pagination-left">
            <span class="pagination-summary">
              Showing {{ (reservationsPagination.page - 1) * reservationsPagination.per_page + 1 }} 
              to {{ Math.min(reservationsPagination.page * reservationsPagination.per_page, reservationsPagination.total) }} 
              of {{ reservationsPagination.total }} reservations
            </span>
          </div>
          
          <div class="pagination-center">
            <button 
              @click="changePage(reservationsPagination.page - 1)" 
              :disabled="reservationsPagination.page <= 1"
              class="pagination-btn"
            >
              <i class="fas fa-chevron-left"></i> Previous
            </button>
            
            <span class="pagination-info">
              Page {{ reservationsPagination.page }} of {{ reservationsPagination.pages }}
            </span>
            
            <button 
              @click="changePage(reservationsPagination.page + 1)" 
              :disabled="reservationsPagination.page >= reservationsPagination.pages"
              class="pagination-btn"
            >
              Next <i class="fas fa-chevron-right"></i>
            </button>
          </div>
          
          <div class="pagination-right">
            <label class="per-page-selector">
              Per page:
              <select v-model.number="reservationsPagination.per_page" @change="changePerPage" class="per-page-select">
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select>
            </label>
          </div>
        </div>
      </div>
      
      <div v-else-if="!reservationsLoading && !reservations.length" class="empty-state">
        <i class="fas fa-calendar-times"></i>
        <h3>No reservations found</h3>
        <p>No reservations match the current filter criteria</p>
      </div>
    </div>

    <!-- Reservation Detail Modal -->
    <Modal 
      :show="showReservationDetailModal" 
      title="Reservation Details" 
      @close="closeReservationDetailModal"
      hide-actions
    >
      <ReservationDetailModal :reservation="selectedReservation" />
    </Modal>

    <!-- Parking Visualization Tab -->
    <div v-if="activeTab === 'visualization'" class="tab-content">
      <!-- <h2>Parking Lot Visualization</h2> -->
      <div v-if="visualizationLoading" class="loading">Loading parking lots...</div>
      <div v-else-if="visualizationError" class="error">{{ visualizationError }}</div>
      <parking-lot-visualizer v-else :parking-lots="visualizationData" @refresh-lots="fetchVisualizationData"
        @add-lot="showAddLotModal = true" @lot-menu="editLot" />
    </div>

    <!-- Analytics Tab -->
    <div v-if="activeTab === 'analytics'" class="tab-content">

      <!-- Charts Section -->
      <div class="charts-section">
        <!-- Overall Spot Utilization (Donut) - Small -->
        <div class="chart-container chart-small">
          <h3><i class="fas fa-chart-pie"></i> Overall Spot Utilization</h3>
          <div class="chart-wrapper">
            <canvas ref="overallUtilizationChart"></canvas>
          </div>
        </div>

        <!-- Reservation Status Distribution (Donut) - Small -->
        <div class="chart-container chart-small">
          <h3><i class="fas fa-tasks"></i> Reservation Status Distribution</h3>
          <div class="chart-wrapper">
            <canvas ref="statusChart"></canvas>
          </div>
        </div>

        <!-- Lot Utilization Chart (Bar) - Medium -->
        <div class="chart-container chart-medium">
          <h3><i class="fas fa-chart-bar"></i> Utilization per Parking Lot</h3>
          <div class="chart-wrapper">
            <canvas ref="utilizationChart"></canvas>
          </div>
        </div>

        <!-- Peak Usage Hours (Line) - Medium -->
        <div class="chart-container chart-medium">
          <h3><i class="fas fa-clock"></i> Peak Usage Hours (All Time)</h3>
          <div class="chart-wrapper">
            <canvas ref="peakHoursChart"></canvas>
          </div>
        </div>

        <!-- Daily Usage Trends (Line) - Large -->
        <div class="chart-container chart-large">
          <h3><i class="fas fa-chart-line"></i> Daily Usage Trends (Past Week)</h3>
          <div class="chart-wrapper">
            <canvas ref="activityChart"></canvas>
          </div>
        </div>

        <!-- Parking Duration Distribution (Bar) - Medium -->
        <div class="chart-container chart-medium">
          <h3><i class="fas fa-hourglass-half"></i> Parking Duration Distribution (Last 7 Days)</h3>
          <div class="chart-wrapper">
            <canvas ref="durationChart"></canvas>
          </div>
        </div>

        <!-- Revenue Chart (Bonus) - Large -->
        <div class="chart-container chart-large">
          <h3><i class="fas fa-rupee-sign"></i> Revenue Trend (Last 30 Days)</h3>
          <div class="chart-wrapper">
            <canvas ref="revenueChart"></canvas>
          </div>
        </div>
      </div>


    </div>

    <!-- Task Management Tab -->
    <div v-if="activeTab === 'tasks'" class="tab-content">
      <!-- Data Consistency Check -->
      <div class="consistency-check-section">
        <h3><i class="fas fa-database"></i> Data Consistency Check</h3>
        <p>Check and fix inconsistencies between parking spots and reservations</p>
        <div class="consistency-actions">
          <button 
            @click="checkDataConsistency" 
            :disabled="consistencyStatus === 'checking'"
            class="task-btn check-btn"
          >
            <i :class="consistencyStatus === 'checking' ? 'fas fa-spinner fa-spin' : 'fas fa-search'"></i>
            {{ consistencyStatus === 'checking' ? 'Checking...' : 'Check Consistency' }}
          </button>
          <button 
            v-if="consistencyIssues && consistencyIssues.length > 0"
            @click="fixDataConsistency" 
            :disabled="consistencyStatus === 'fixing'"
            class="task-btn fix-btn"
          >
            <i :class="consistencyStatus === 'fixing' ? 'fas fa-spinner fa-spin' : 'fas fa-wrench'"></i>
            {{ consistencyStatus === 'fixing' ? 'Fixing...' : `Fix ${consistencyIssues.length} Issues` }}
          </button>
        </div>
        <div v-if="consistencyResult" class="consistency-result">
          <div v-if="consistencyIssues && consistencyIssues.length > 0" class="issues-found">
            <h4><i class="fas fa-exclamation-triangle"></i> Issues Found: {{ consistencyIssues.length }}</h4>
            <ul>
              <li v-for="(issue, index) in consistencyIssues.slice(0, 5)" :key="index">
                {{ issue.message }}
              </li>
              <li v-if="consistencyIssues.length > 5">
                ... and {{ consistencyIssues.length - 5 }} more issues
              </li>
            </ul>
          </div>
          <div v-else class="no-issues">
            <i class="fas fa-check-circle"></i> No consistency issues found!
          </div>
          <div v-if="consistencyFixesApplied && consistencyFixesApplied.length > 0" class="fixes-applied">
            <h4><i class="fas fa-check"></i> Fixes Applied: {{ consistencyFixesApplied.length }}</h4>
            <ul>
              <li v-for="(fix, index) in consistencyFixesApplied" :key="index">
                {{ fix }}
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <div class="background-tasks-header">
        <div class="section-header">
          <div class="section-title-group">
            <h2 class="section-title">
              <i class="fas fa-cogs"></i>
              Background Tasks
            </h2>
            <p class="section-description">
              These automations run on schedule. Trigger them manually anytime.
            </p>
          </div>
        </div>
      </div>

      <div class="task-sections">
        <div class="task-grid">
          <div class="task-card" v-for="task in taskCatalog" :key="task.key">
            <div class="task-card-header">
              <h3><i :class="task.icon"></i> {{ task.title }}</h3>
            </div>
            <p class="task-description">{{ task.description }}</p>
            <button 
              @click="triggerTask(task.key)" 
              :disabled="taskStatus[task.key] === 'running'"
              class="task-btn"
            >
              {{ taskStatus[task.key] === 'running' ? task.runningText : task.buttonText }}
            </button>
            <div v-if="shouldShowTaskResult(task.key)" class="task-result">
              <span v-html="taskResults[task.key]"></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Lot Modal - Available from any tab -->
    <div v-if="showAddLotModal || showEditLotModal" class="modal-overlay">
      <div class="modal lot-modal">
        <h3>{{ showEditLotModal ? 'Edit' : 'Add' }} Parking Lot</h3>
        <form @submit.prevent="showEditLotModal ? updateLot() : addLot()" class="lot-form">
          <div class="form-grid">
            <label class="full-width">
              Parking Name:
              <input v-model="lotForm.name" required placeholder="e.g., Downtown Parking" />
            </label>
            <label class="full-width">
              Address:
              <input v-model="lotForm.address" required placeholder="Full address" />
            </label>
            <label>
              Pincode:
              <input v-model="lotForm.pincode" required pattern="[0-9]{6}" maxlength="6" placeholder="6-digit pincode" />
            </label>
            <label>
              Price (₹/hour):
              <input type="number" v-model.number="lotForm.price" min="0" step="1" required placeholder="e.g., 50" />
            </label>
            <label>
              Capacity (Spots):
              <input type="number" v-model.number="lotForm.capacity" min="1" required />
            </label>
            <label>
              Opening Time:
              <input type="time" v-model="lotForm.available_from" required />
            </label>
            <label>
              Closing Time:
              <input type="time" v-model="lotForm.available_to" required />
            </label>
          </div>
          <div class="modal-actions">
            <button type="submit" class="submit-btn">{{ showEditLotModal ? 'Update' : 'Add' }}</button>
            <button type="button" @click="closeLotModal" class="cancel-btn">Cancel</button>
          </div>
        </form>
      </div>
      </div>
    </div>
    

  </div>
</template>

<script>
import ParkingLotVisualizer from '../../components/admin/ParkingLotVisualizer.vue';
import Modal from '../../components/common/Modal.vue';
import ReservationDetailModal from '../../components/admin/ReservationDetailModal.vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  LineController,
  BarController,
  DoughnutController,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  LineController,
  BarController,
  DoughnutController,
  Title,
  Tooltip,
  Legend,
  Filler
)

export default {
  name: "AdminDashboard",
  components: {
    ParkingLotVisualizer,
    Modal,
    ReservationDetailModal
  },
  data() {
    return {
      activeTab: this.$route.query.tab || 'lots',
      activeMenu: null, // Track which card's menu is open
      // Parking Lots
      lots: [],
      filteredLots: [],
      lotsSearchQuery: '',
      lotsLoading: false,
      lotsError: '',
      showAddLotModal: false,
      showEditLotModal: false,
      lotForm: {
        id: null,
        name: '',
        address: '',
        pincode: '',
        capacity: 1,
        price: 50,
        available_from: '06:00',
        available_to: '22:00'
      },
      // Users
      users: [],
      filteredUsers: [],
      usersSearchQuery: '',
      showAddUserModal: false,
      showEditUserModal: false,
      showUserDetailModal: false,
      showFlaggedUsersModal: false,
      selectedUser: null,
      userDetails: {},
      userDetailsLoading: false,
      activeUserTab: 'info',
      flaggedUsers: [],
      flaggedUsersLoading: false,
      userForm: {
        id: null,
        email: '',
        username: '',
        password: '',
        roles: ''
      },
      // Reservations
      reservations: [],
      reservationsLoading: false,
      reservationsError: '',
      reservationsExportLoading: false,
      reservationsExportStatus: null,
      reservationFilter: 'all',
      reservationsPagination: {
        page: 1,
        per_page: 20,
        total: 0,
        pages: 0
      },
      showReservationDetailModal: false,
      selectedReservation: null,
      // Analytics
      analytics: {
        overview: {},
        revenue_chart: [],
        lot_utilization: [],
        daily_activity: [],
        top_users: [],
        peak_hours: [],
        duration_distribution: [],
        status_distribution: []
      },
      charts: {
        revenue: null,
        utilization: null,
        activity: null,
        overallUtilization: null,
        peakHours: null,
        duration: null,
        status: null
      },
      // Visualization
      visualizationData: [],
      visualizationLoading: false,
      visualizationError: null,
      // Data Consistency
      consistencyStatus: 'idle',
      consistencyResult: null,
      consistencyIssues: [],
      consistencyFixesApplied: [],
      // Task Management
      taskStatus: {
        download_csv_report: 'idle',
        cleanup_old_csv_files: 'idle',
        system_health_check: 'idle',
        auto_release_expired_reservations: 'idle',
        daily_update: 'idle'
      },
      taskResults: {
        download_csv_report: null,
        cleanup_old_csv_files: null,
        system_health_check: null,
        auto_release_expired_reservations: null,
        daily_update: null
      },
      // User export
      usersExportLoading: false,
      usersExportStatus: null,
      taskLogs: [],
      showTaskLogs: false,
      taskCatalog: [
        {
          key: 'cleanup_old_csv_files',
          title: 'CSV Cleanup',
          schedule: 'Scheduled daily at 2:00 AM',
          icon: 'fas fa-trash-alt',
          type: 'instant',
          buttonText: 'Cleanup Files',
          runningText: 'Cleaning...'
        },
        {
          key: 'system_health_check',
          title: 'Health Check',
          schedule: 'Scheduled daily at 2:00 AM',
          icon: 'fas fa-heartbeat',
          type: 'instant',
          buttonText: 'Run Health Check',
          runningText: 'Checking...'
        },
        {
          key: 'auto_release_expired_reservations',
          title: 'Release Expired',
          schedule: 'Scheduled hourly',
          icon: 'fas fa-clock',
          type: 'instant',
          buttonText: 'Release Spots',
          runningText: 'Processing...'
        },
        {
          key: 'daily_update',
          title: 'Daily Maintenance',
          schedule: 'Scheduled daily at 2:00 AM',
          icon: 'fas fa-wrench',
          type: 'background',
          buttonText: 'Run Maintenance',
          runningText: 'Running...'
        }
      ]
    };
  },
  created() {
    this.fetchLots();
    this.fetchUsers();
    this.fetchTaskLogs();
    
    // Poll for task logs every 30 seconds
    setInterval(() => {
      this.fetchTaskLogs();
    }, 30000);
    this.fetchAnalytics(); // Fetch analytics data on component load
    this.loadTaskLogs();
  },
  beforeUnmount() {
    this.destroyCharts();
    // Remove click outside listener
    document.removeEventListener('click', this.handleClickOutside);
  },
  watch: {
    activeTab(newTab) {
      // Update URL query parameter to persist tab state
      this.$router.replace({ query: { ...this.$route.query, tab: newTab } });
      
      if (newTab === 'analytics' || newTab === 'users') {
        this.fetchAnalytics();
      }
      if (newTab === 'visualization') {
        this.fetchVisualizationData();
      }
      if (newTab === 'reservations') {
        this.fetchReservations();
      }
    }
  },
  mounted() {
    // Fetch data for the initial active tab (only for tabs not already fetched in created)
    if (this.activeTab === 'visualization') {
      this.fetchVisualizationData();
    } else if (this.activeTab === 'reservations') {
      this.fetchReservations();
    }
    // Add click outside listener for menu
    document.addEventListener('click', this.handleClickOutside);
  },
  computed: {
    instantTasks() {
      return this.taskCatalog.filter(task => task.type === 'instant');
    },
    backgroundTasks() {
      return this.taskCatalog.filter(task => task.type === 'background');
    }
  },
  methods: {
    formatInteger(value) {
      if (value === null || value === undefined) return '0';
      // Use Math.trunc to remove decimal part without rounding
      return Math.trunc(value);
    },
    formatTaskResult(taskName, payload) {
      if (!payload) return 'Task completed successfully';

      if (taskName === 'download_csv_report') {
        if (payload.download_url || payload.file_path) {
          const label = payload.filename || 'Download PDF';
          const downloadPath = payload.download_url || payload.file_path;
          return `${payload.message || 'Analytics PDF ready'} - <a href="http://localhost:5000${downloadPath}" target="_blank" download>${label}</a>`;
        }
        return payload.message || 'Analytics PDF generated';
      }

      if (taskName === 'system_health_check') {
        const summary = payload.summary || payload.message || 'Health check complete';
        const utilization = payload.utilization_percent !== undefined ? ` | Utilization: ${payload.utilization_percent}%` : '';
        const active = payload.overview && payload.overview.active_reservations !== undefined
          ? ` | Active Reservations: ${payload.overview.active_reservations}`
          : '';
        return `${summary}${utilization}${active}`;
      }

      if (taskName === 'daily_update') {
        const cleanup = payload.csv_cleanup?.status || 'unknown';
        const released = payload.auto_release?.released_count ?? '0';
        return `CSV cleanup: ${cleanup} | Spots released: ${released}`;
      }

      if (taskName === 'auto_release_expired_reservations') {
        const released = payload.released_count ?? 0;
        return `${payload.message || 'Auto-release completed'} | Spots released: ${released}`;
      }

      if (taskName === 'cleanup_old_csv_files') {
        const deleted = payload.deleted_count ?? 0;
        return `${payload.message || 'Cleanup completed'} | Files removed: ${deleted}`;
      }

      if (payload.message) return payload.message;
      if (payload.status && payload.task_id) {
        return `Task ${payload.status}. ID: ${payload.task_id}`;
      }
      if (payload.status) {
        return `Status: ${payload.status}`;
      }
      try {
        return JSON.stringify(payload);
      } catch (err) {
        return 'Task completed successfully';
      }
    },
    async exportReservationsCSV() {
      this.reservationsExportLoading = true;
      this.reservationsExportStatus = null;
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/reservations/export', {
          method: 'POST',
          headers: {
            'auth-token': token,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ status: this.reservationFilter })
        });

        if (response.ok) {
          const data = await response.json();
          const emailSent = typeof data.email_sent === 'boolean' ? data.email_sent : true;
          const title = emailSent ? 'Export Started' : 'Email Delivery Issue';
          const message = data.task_message || data.message;
          this.reservationsExportStatus = {
            title,
            message,
            email_sent: emailSent,
            email_message: data.email_message,
            download_url: data.download_url,
            filename: data.filename,
            filter: data.filter || this.reservationFilter
          };
          this.$toast[emailSent ? 'success' : 'info'](message);
        } else {
          const errorData = await response.json();
          this.reservationsExportStatus = {
            title: 'Export Failed',
            message: errorData.error || 'Failed to start export',
            email_sent: false
          };
          this.$toast.error(errorData.error || 'Failed to start export');
        }
      } catch (err) {
        this.$toast.error('Error starting export. Please try again.');
      } finally {
        this.reservationsExportLoading = false;
      }
    },
    scheduleTaskReset(taskName, delay = 10000) {
      setTimeout(() => {
        this.taskResults[taskName] = null;
        this.taskStatus[taskName] = 'idle';
      }, delay);
    },
    // --- Parking Lots CRUD ---
    async fetchLots() {
      this.lotsLoading = true;
      this.lotsError = '';
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/parking_lots', {
          headers: { 'auth-token': token }
        });
        if (response.ok) {
          const data = await response.json();
          console.log('Raw parking lot data from backend:', data);
          // Map backend fields to frontend fields
          this.lots = data.map(lot => {
            console.log('Mapping lot:', lot);
            return {
              id: lot.id,
              name: lot.location, // maps to prime_location_name in backend
              location: lot.address, // maps to address in backend
              capacity: lot.total_spots,
              available_spots: lot.available_spots,
              occupied_spots: lot.occupied_spots,
              price: lot.price,
              pincode: lot.pincode,
              available_from: lot.available_from,
              available_to: lot.available_to,
              is_active: lot.is_active
            };
          });
          this.filteredLots = [...this.lots];
        } else {
          this.lots = [];
          this.filteredLots = [];
          this.lotsError = 'Failed to fetch lots.';
        }
      } catch (err) {
        this.lots = [];
        this.filteredLots = [];
        this.lotsError = 'Error fetching lots.';
      } finally {
        this.lotsLoading = false;
      }
    },
    
    filterLots() {
      if (!this.lotsSearchQuery.trim()) {
        this.filteredLots = [...this.lots];
        return;
      }
      
      const query = this.lotsSearchQuery.toLowerCase();
      this.filteredLots = this.lots.filter(lot => {
        return (
          lot.name.toLowerCase().includes(query) ||
          lot.location.toLowerCase().includes(query) ||
          lot.pincode.toLowerCase().includes(query)
        );
      });
    },
    
    clearLotsSearch() {
      this.lotsSearchQuery = '';
    },
    async addLot() {
      this.lotsError = '';
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/parking_lots', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          },
          body: JSON.stringify({
            prime_location_name: this.lotForm.name,
            address: this.lotForm.address,
            pincode: this.lotForm.pincode,
            price: this.lotForm.price,
            number_of_spots: this.lotForm.capacity,
            available_from: this.lotForm.available_from,
            available_to: this.lotForm.available_to
          })
        });
        if (response.ok) {
          await this.fetchLots(); // refresh list for lots tab

          // If we're on the visualization tab, also refresh visualization data
          if (this.activeTab === 'visualization') {
            await this.fetchVisualizationData();
          }

          this.closeLotModal();
        } else {
          this.lotsError = 'Failed to add lot.';
        }
      } catch (err) {
        this.lotsError = 'Error adding lot.';
      }
    },
    async editLot(lot) {
      console.log('Editing lot:', lot); // Debug log
      
      // If lot data is incomplete (from visualization), fetch full details
      if (!lot.price || !lot.pincode || !lot.available_from) {
        try {
          const token = localStorage.getItem('auth-token');
          const response = await fetch(`http://localhost:5000/api/admin/parking_lots/${lot.id}`, {
            headers: { 'auth-token': token }
          });
          
          if (response.ok) {
            const fullLot = await response.json();
            lot = fullLot; // Replace with full data
          }
        } catch (err) {
          console.error('Error fetching lot details:', err);
        }
      }
      
      this.lotForm = {
        id: lot.id,
        name: lot.name || '',
        address: lot.location || '',
        pincode: lot.pincode || '',
        capacity: lot.capacity || 1,
        price: lot.price || 50,
        available_from: lot.available_from || '06:00',
        available_to: lot.available_to || '22:00'
      };
      console.log('Form populated with:', this.lotForm); // Debug log
      this.showEditLotModal = true;
    },
    async updateLot() {
      this.lotsError = '';
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/parking_lots/${this.lotForm.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          },
          body: JSON.stringify({
            prime_location_name: this.lotForm.name,
            address: this.lotForm.address,
            pincode: this.lotForm.pincode,
            price: this.lotForm.price,
            number_of_spots: this.lotForm.capacity,
            available_from: this.lotForm.available_from,
            available_to: this.lotForm.available_to
          })
        });
        if (response.ok) {
          await this.fetchLots(); // refresh list
          
          // If we're on the visualization tab, also refresh visualization data
          if (this.activeTab === 'visualization') {
            await this.fetchVisualizationData();
          }
          
          this.closeLotModal();
        } else {
          this.lotsError = 'Failed to update lot.';
        }
      } catch (err) {
        this.lotsError = 'Error updating lot.';
      }
    },
    async deleteLot(id) {
      const lot = this.lots.find(l => l.id === id);
      if (lot && (lot.occupied_spots > 0 || lot.available_spots !== lot.capacity)) {
        this.$toast.error('Cannot delete a parking lot with active reservations or occupied spots.');
        return;
      }

      if (!confirm('Are you sure you want to delete this parking lot?')) {
        return;
      }
      this.lotsError = '';
      try {
        const token = localStorage.getItem('auth-token');
        console.log('Attempting to delete lot:', id, 'with token:', token ? 'present' : 'missing');

        // Create an AbortController for timeout handling
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        const response = await fetch(`http://localhost:5000/api/admin/parking_lots/${id}`, {
          method: 'DELETE',
          headers: {
            'auth-token': token,
            'Content-Type': 'application/json'
          },
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        console.log('Delete response status:', response.status);
        console.log('Delete response ok:', response.ok);
        console.log('Delete response headers:', response.headers);

        if (response.ok) {
          const result = await response.json();
          console.log('Delete success result:', result);

          await this.fetchLots(); // refresh list

          // If we're on the visualization tab, also refresh visualization data
          if (this.activeTab === 'visualization') {
            await this.fetchVisualizationData();
          }

          // Show success message
          this.$toast.success('Parking lot deleted successfully!');
        } else {
          // Try to get error message from response
          let errorMessage = `Failed to delete lot. Status: ${response.status}`;
          try {
            const errorData = await response.json();
            console.log('Delete error data:', errorData);
            errorMessage = errorData.error || errorMessage;
          } catch (jsonError) {
            console.log('Could not parse error response as JSON:', jsonError);
            // Try to get response as text
            try {
              const errorText = await response.text();
              console.log('Delete error text:', errorText);
              if (errorText) {
                errorMessage = `${errorMessage} - ${errorText}`;
              }
            } catch (textError) {
              console.log('Could not get error response as text:', textError);
            }
          }
          this.lotsError = errorMessage;
          this.$toast.error(errorMessage);
        }
      } catch (err) {
        console.error('Delete fetch error details:', {
          message: err.message,
          name: err.name,
          stack: err.stack
        });

        // Provide more specific error messages based on error type
        let errorMessage = 'Error deleting lot: ';
        if (err.name === 'TypeError' && err.message.includes('Failed to fetch')) {
          errorMessage += 'Network error - please check if the backend server is running on http://localhost:5000';
        } else if (err.name === 'AbortError') {
          errorMessage += 'Request was cancelled or timed out';
        } else {
          errorMessage += err.message;
        }

        this.lotsError = errorMessage;
        this.$toast.error(errorMessage);
      }
    },
    closeLotModal() {
      this.showAddLotModal = false;
      this.showEditLotModal = false;
      this.lotForm = { 
        id: null, 
        name: '', 
        address: '', 
        pincode: '', 
        capacity: 1, 
        price: 50, 
        available_from: '06:00', 
        available_to: '22:00' 
      };
    },
    toggleMenu(lotId) {
      this.activeMenu = this.activeMenu === lotId ? null : lotId;
    },
    handleClickOutside(event) {
      if (!event.target.closest('.lot-card-menu')) {
        this.activeMenu = null;
      }
    },
    async toggleLotStatus(lot) {
      const action = lot.is_active ? 'deactivate' : 'activate';

      // Prevent deactivating if there are occupied spots or reservations
      if (lot.is_active && (lot.occupied_spots > 0 || lot.available_spots !== lot.capacity)) {
        this.$toast.error('Cannot deactivate a parking lot with active reservations or occupied spots.');
        return;
      }

      if (!confirm(`Are you sure you want to ${action} this parking lot?`)) {
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
          lot.is_active = result.lot.is_active;
          
          // Show success message
          this.$toast.success(result.message);
        } else {
          const errorData = await response.json();
          this.$toast.error(errorData.error || `Failed to ${action} parking lot`);
        }
      } catch (err) {
        console.error(`Error ${action}ing parking lot:`, err);
        this.$toast.error(`Error ${action}ing parking lot. Please try again.`);
      }
    },

    // --- Users CRUD ---
    async fetchUsers() {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/users', {
          headers: { 'auth-token': token }
        });
        
        if (response.ok) {
          const data = await response.json();
          this.users = data.map(user => ({
            id: user.id,
            email: user.email,
            username: user.username,
            first_name: user.first_name || '',
            last_name: user.last_name || '',
            active: user.active,
            is_flagged: user.is_flagged || false,
            created_at: user.created_at,
            roles: user.roles ? user.roles.map(role => role.name) : ['user']
          }));
          this.filteredUsers = [...this.users];
        } else {
          console.error('Failed to fetch users');
          this.users = [];
          this.filteredUsers = [];
        }
      } catch (err) {
        console.error('Error fetching users:', err);
        this.users = [];
        this.filteredUsers = [];
      }
    },
    
    filterUsers() {
      if (!this.usersSearchQuery.trim()) {
        this.filteredUsers = [...this.users];
        return;
      }
      
      const query = this.usersSearchQuery.toLowerCase();
      this.filteredUsers = this.users.filter(user => {
        const fullName = `${user.first_name} ${user.last_name}`.toLowerCase();
        return (
          fullName.includes(query) ||
          user.email.toLowerCase().includes(query) ||
          user.username.toLowerCase().includes(query)
        );
      });
    },
    
    clearUsersSearch() {
      this.usersSearchQuery = '';
      this.filteredUsers = [...this.users];
    },
    async exportUsersCSV() {
      this.usersExportLoading = true;
      this.usersExportStatus = null;
      
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/users/export', {
          method: 'POST',
          headers: {
            'auth-token': token,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            admin_email: null // Will use current user's email from backend
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          const taskStatus = data.task_status || data.status || 'started';
          const taskMessage = data.task_message || data.message;
          const emailSent = typeof data.email_sent === 'boolean' ? data.email_sent : true;
          const toastVariant = emailSent ? 'success' : 'warning';
          const toastTitle = emailSent ? 'Export Started' : 'Email Delivery Issue';
          const toastMessage = emailSent
            ? `User data export started. You will receive an email at ${data.admin_email} when the CSV is ready.`
            : (data.email_message || 'CSV generated but email could not be sent. You can download it from the dashboard.');

          this.usersExportStatus = {
            message: taskMessage,
            status: taskStatus,
            admin_email: data.admin_email,
            email_sent: emailSent,
            email_message: data.email_message,
            download_url: data.download_url,
            filename: data.filename
          };

          if (data.download_url && !emailSent) {
            console.warn('Email delivery failed. CSV available at:', data.download_url);
          }

          this.$toast[toastVariant === 'warning' ? 'info' : toastVariant](toastMessage);
        } else {
          const errorData = await response.json();
          this.usersExportStatus = {
            message: errorData.error || 'Failed to start export',
            status: 'error'
          };
          this.$toast.error(errorData.error || 'Failed to start export');
        }
      } catch (err) {
        console.error('Error exporting users:', err);
        this.usersExportStatus = {
          message: err.message || 'Error starting export',
          status: 'error'
        };
        this.$toast.error('Error starting export. Please try again.');
      } finally {
        this.usersExportLoading = false;
      }
    },
    async addUser() {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/users', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          },
          body: JSON.stringify({
            email: this.userForm.email,
            username: this.userForm.username,
            password: this.userForm.password,
            first_name: this.userForm.first_name || '',
            last_name: this.userForm.last_name || '',
            roles: this.userForm.roles.split(',').map(r => r.trim())
          })
        });

        if (response.ok) {
          const data = await response.json();
          this.$toast.success(data.message || 'User created successfully!');
          await this.fetchUsers(); // Refresh users list
          this.closeUserModal();
        } else {
          const errorData = await response.json();
          this.$toast.error(errorData.error || 'Failed to create user');
        }
      } catch (err) {
        console.error('Error creating user:', err);
        this.$toast.error('Error creating user. Please try again.');
      }
    },
    editUser(user) {
      this.userForm = {
        id: user.id,
        email: user.email,
        username: user.username,
        password: '',
        roles: user.roles.join(', ')
      };
      this.showEditUserModal = true;
    },
    async updateUser() {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/users/${this.userForm.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          },
          body: JSON.stringify({
            email: this.userForm.email,
            username: this.userForm.username,
            first_name: this.userForm.first_name || '',
            last_name: this.userForm.last_name || '',
            roles: this.userForm.roles.split(',').map(r => r.trim())
          })
        });

        if (response.ok) {
          const data = await response.json();
          this.$toast.success(data.message || 'User updated successfully!');
          await this.fetchUsers(); // Refresh users list
          this.closeUserModal();
        } else {
          const errorData = await response.json();
          this.$toast.error(errorData.error || 'Failed to update user');
        }
      } catch (err) {
        console.error('Error updating user:', err);
        this.$toast.error('Error updating user. Please try again.');
      }
    },
    async deleteUser(id) {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/users/${id}`, {
          method: 'DELETE',
          headers: {
            'auth-token': token,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          this.$toast.success(data.message || 'User deleted successfully!');
          await this.fetchUsers(); // Refresh users list
        } else {
          const errorData = await response.json();
          this.$toast.error(errorData.error || 'Failed to delete user');
        }
      } catch (err) {
        console.error('Error deleting user:', err);
        this.$toast.error('Error deleting user. Please try again.');
      }
    },
    closeUserModal() {
      this.showAddUserModal = false;
      this.showEditUserModal = false;
      this.userForm = { id: null, email: '', username: '', password: '', roles: '' };
    },

    // --- Reservations Methods ---
    async fetchReservations() {
      this.reservationsLoading = true;
      this.reservationsError = '';
      try {
        const token = localStorage.getItem('auth-token');
        const params = new URLSearchParams({
          page: this.reservationsPagination.page,
          per_page: this.reservationsPagination.per_page,
          status: this.reservationFilter
        });
        
        const response = await fetch(`http://localhost:5000/api/admin/reservations?${params}`, {
          headers: { 'auth-token': token }
        });
        
        if (response.ok) {
          const data = await response.json();
          this.reservations = data.reservations;
          this.reservationsPagination = data.pagination;
        } else {
          this.reservations = [];
          this.reservationsError = 'Failed to fetch reservations.';
        }
      } catch (err) {
        this.reservations = [];
        this.reservationsError = 'Error fetching reservations.';
      } finally {
        this.reservationsLoading = false;
      }
    },
    showReservationDetails(reservation) {
      this.selectedReservation = reservation;
      this.showReservationDetailModal = true;
    },
    closeReservationDetailModal() {
      this.showReservationDetailModal = false;
      this.selectedReservation = null;
    },
    changePage(page) {
      if (page >= 1 && page <= this.reservationsPagination.pages) {
        this.reservationsPagination.page = page;
        this.fetchReservations();
      }
    },
    changePerPage() {
      this.reservationsPagination.page = 1; // Reset to first page when changing per_page
      this.fetchReservations();
    },
    formatDateTime(dateTimeStr) {
      if (!dateTimeStr) return 'N/A';
      const date = new Date(dateTimeStr);
      return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    formatTimeOnly(dateTimeStr) {
      if (!dateTimeStr) return '--:--';
      return new Date(dateTimeStr).toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    formatDateOnly(dateTimeStr) {
      if (!dateTimeStr) return '';
      return new Date(dateTimeStr).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },
    formatDuration(reservation) {
      if (!reservation) return '-';
      const { parking_timestamp: startTs, leaving_timestamp: endTs, duration_hours } = reservation;

      if (startTs && endTs) {
        const start = new Date(startTs);
        const end = new Date(endTs);
        const diffMs = Math.max(end - start, 0);
        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        return `${hours}h ${minutes}m`;
      }

      if (typeof duration_hours === 'number') {
        const hours = Math.floor(duration_hours);
        const minutes = Math.round((duration_hours - hours) * 60);
        return `${hours}h ${minutes}m`;
      }

      return '-';
    },
    formatDate(dateStr) {
      if (!dateStr) return 'N/A';
      const date = new Date(dateStr);
      return date.toLocaleDateString();
    },
    async showUserDetails(user) {
      this.selectedUser = user;
      this.showUserDetailModal = true;
      this.activeUserTab = 'info';
      await this.fetchUserDetails(user.id);
    },
    closeUserDetailModal() {
      this.showUserDetailModal = false;
      this.selectedUser = null;
      this.userDetails = {};
      this.userDetailsLoading = false;
    },
    async fetchUserDetails(userId) {
      this.userDetailsLoading = true;
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/users/${userId}/details`, {
          headers: { 'auth-token': token }
        });
        
        if (response.ok) {
          this.userDetails = await response.json();
        } else {
          console.error('Failed to fetch user details');
        }
      } catch (err) {
        console.error('Error fetching user details:', err);
      } finally {
        this.userDetailsLoading = false;
      }
    },
    async fetchFlaggedUsers() {
      this.flaggedUsersLoading = true;
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/users/flagged', {
          headers: { 'auth-token': token }
        });
        
        if (response.ok) {
          const data = await response.json();
          this.flaggedUsers = data.flagged_users;
        } else {
          console.error('Failed to fetch flagged users');
        }
      } catch (err) {
        console.error('Error fetching flagged users:', err);
      } finally {
        this.flaggedUsersLoading = false;
      }
    },
    async openFlaggedUsersModal() {
      this.showFlaggedUsersModal = true;
      await this.fetchFlaggedUsers();
    },
    closeFlaggedUsersModal() {
      this.showFlaggedUsersModal = false;
      this.flaggedUsers = [];
    },
    async toggleUserFlag(userId) {
      const user = this.userDetails.user;
      const action = user.is_flagged ? 'unflag' : 'flag';

      try {
        const token = localStorage.getItem('auth-token');
        const method = user.is_flagged ? 'DELETE' : 'POST';
        const response = await fetch(`http://localhost:5000/api/admin/users/${userId}/flag`, {
          method: method,
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          }
        });

        if (response.ok) {
          const result = await response.json();
          // Update local data
          this.userDetails.user.is_flagged = result.user.is_flagged;
          this.$toast.success(result.message);
        } else {
          const errorData = await response.json();
          this.$toast.error(errorData.error || `Failed to ${action} user`);
        }
      } catch (err) {
        console.error(`Error ${action}ing user:`, err);
        this.$toast.error(`Error ${action}ing user. Please try again.`);
      }
    },
    async toggleUserActive(userId) {
      const user = this.userDetails.user;
      const action = user.active ? 'deactivate' : 'activate';

      if (!confirm(`Are you sure you want to ${action} this user?`)) {
        return;
      }

      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/users/${userId}/toggle-active`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          }
        });

        if (response.ok) {
          const result = await response.json();
          // Update local data
          this.userDetails.user.active = result.user.active;
          this.$toast.success(result.message);
        } else {
          const errorData = await response.json();
          this.$toast.error(errorData.error || `Failed to ${action} user`);
        }
      } catch (err) {
        console.error(`Error ${action}ing user:`, err);
        this.$toast.error(`Error ${action}ing user. Please try again.`);
      }
    },
    async unflagUser(userId) {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/users/${userId}/flag`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'auth-token': token
          }
        });

        if (response.ok) {
          const result = await response.json();
          // Remove from flagged users list
          this.flaggedUsers = this.flaggedUsers.filter(user => user.id !== userId);
          this.$toast.success(result.message);
        } else {
          const errorData = await response.json();
          this.$toast.error(errorData.error || 'Failed to unflag user');
        }
      } catch (err) {
        console.error('Error unflagging user:', err);
        this.$toast.error('Error unflagging user. Please try again.');
      }
    },
    logout() {
      localStorage.removeItem('auth-token');
      this.$router.push('/login');
    },

    // --- Analytics Methods ---
    async fetchAnalytics() {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/analytics/dashboard', {
          headers: { 'auth-token': token }
        });

        if (response.ok) {
          this.analytics = await response.json();
          this.$nextTick(() => {
            this.createCharts();
          });
        } else {
          console.error('Failed to fetch analytics');
        }
      } catch (err) {
        console.error('Error fetching analytics:', err);
      }
    },

    createCharts() {
      this.createOverallUtilizationChart();
      this.createUtilizationChart();
      this.createPeakHoursChart();
      this.createActivityChart();
      this.createDurationChart();
      this.createStatusChart();
      this.createRevenueChart();
    },

    createRevenueChart() {
      const ctx = this.$refs.revenueChart?.getContext('2d');
      if (!ctx || !this.analytics.revenue_chart) return;

      // Destroy existing chart
      if (this.charts.revenue) {
        this.charts.revenue.destroy();
      }

      const data = this.analytics.revenue_chart;
      const labels = data.map(d => new Date(d.date).toLocaleDateString());
      const revenues = data.map(d => d.revenue);

      this.charts.revenue = new ChartJS(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Revenue (₹)',
            data: revenues,
            borderColor: '#1976d2',
            backgroundColor: 'rgba(25, 118, 210, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: 'index'
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: '#1976d2',
              borderWidth: 1,
              cornerRadius: 8,
              displayColors: false,
              callbacks: {
                label: function(context) {
                  return 'Revenue: ₹' + context.parsed.y.toFixed(2);
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: '#666',
                font: {
                  size: 12
                }
              }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.1)'
              },
              ticks: {
                color: '#666',
                font: {
                  size: 12
                },
                callback: function(value) {
                  return '₹' + value.toFixed(0);
                }
              }
            }
          },
          elements: {
            point: {
              radius: 4,
              hoverRadius: 6
            }
          }
        }
      });
    },

    createUtilizationChart() {
      const ctx = this.$refs.utilizationChart?.getContext('2d');
      if (!ctx || !this.analytics.lot_utilization) return;

      // Destroy existing chart
      if (this.charts.utilization) {
        this.charts.utilization.destroy();
      }

      const data = this.analytics.lot_utilization;
      const labels = data.map(d => d.name);
      const utilization = data.map(d => d.utilization_rate);

      this.charts.utilization = new ChartJS(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Utilization (%)',
            data: utilization,
            backgroundColor: [
              'rgba(67, 160, 71, 0.8)',
              'rgba(255, 152, 0, 0.8)',
              'rgba(244, 67, 54, 0.8)',
              'rgba(156, 39, 176, 0.8)',
              'rgba(33, 150, 243, 0.8)'
            ],
            borderColor: [
              'rgba(67, 160, 71, 1)',
              'rgba(255, 152, 0, 1)',
              'rgba(244, 67, 54, 1)',
              'rgba(156, 39, 176, 1)',
              'rgba(33, 150, 243, 1)'
            ],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: '#43a047',
              borderWidth: 1,
              cornerRadius: 8,
              displayColors: false,
              callbacks: {
                label: function(context) {
                  return 'Utilization: ' + context.parsed.y.toFixed(1) + '%';
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: '#666',
                font: {
                  size: 12
                },
                maxRotation: 45
              }
            },
            y: {
              beginAtZero: true,
              max: 100,
              grid: {
                color: 'rgba(0, 0, 0, 0.1)'
              },
              ticks: {
                color: '#666',
                font: {
                  size: 12
                },
                callback: function(value) {
                  return value + '%';
                }
              }
            }
          }
        }
      });
    },

    createActivityChart() {
      const ctx = this.$refs.activityChart?.getContext('2d');
      if (!ctx || !this.analytics.daily_activity) return;

      // Destroy existing chart
      if (this.charts.activity) {
        this.charts.activity.destroy();
      }

      const data = this.analytics.daily_activity;
      const labels = data.map(d => new Date(d.date).toLocaleDateString());
      const bookings = data.map(d => d.total_bookings);

      this.charts.activity = new ChartJS(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Total Bookings',
            data: bookings,
            borderColor: '#ff9800',
            backgroundColor: 'rgba(255, 152, 0, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#ff9800',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: 'index'
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: '#ff9800',
              borderWidth: 1,
              cornerRadius: 8,
              displayColors: false,
              callbacks: {
                label: function(context) {
                  return 'Bookings: ' + context.parsed.y;
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: '#666',
                font: {
                  size: 12
                }
              }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.1)'
              },
              ticks: {
                color: '#666',
                font: {
                  size: 12
                },
                stepSize: 1,
                callback: function(value) {
                  return Math.floor(value);
                }
              }
            }
          },
          elements: {
            point: {
              radius: 5,
              hoverRadius: 7,
              backgroundColor: '#ff9800',
              borderColor: '#fff',
              borderWidth: 2
            }
          }
        }
      });

    },

    createOverallUtilizationChart() {
      const ctx = this.$refs.overallUtilizationChart?.getContext('2d');
      if (!ctx || !this.analytics.overview) return;

      if (this.charts.overallUtilization) {
        this.charts.overallUtilization.destroy();
      }

      const occupied = this.analytics.overview.total_spots - (this.analytics.overview.available_spots || 0);
      const available = this.analytics.overview.available_spots || 0;

      this.charts.overallUtilization = new ChartJS(ctx, {
        type: 'doughnut',
        data: {
          labels: ['Occupied', 'Available'],
          datasets: [{
            data: [occupied, available],
            backgroundColor: [
              'rgba(255, 99, 132, 0.8)',  // Coral red
              'rgba(75, 192, 192, 0.8)'   // Teal
            ],
            borderColor: ['#fff', '#fff'],
            borderWidth: 3,
            hoverBackgroundColor: [
              'rgba(255, 99, 132, 1)',
              'rgba(75, 192, 192, 1)'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 15,
                font: { size: 12 },
                color: '#666'
              }
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#fff',
              bodyColor: '#fff',
              cornerRadius: 8,
              callbacks: {
                label: function(context) {
                  const total = context.dataset.data.reduce((a, b) => a + b, 0);
                  const percentage = ((context.parsed / total) * 100).toFixed(1);
                  return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                }
              }
            }
          }
        }
      });
    },

    createPeakHoursChart() {
      const ctx = this.$refs.peakHoursChart?.getContext('2d');
      if (!ctx) return;

      if (this.charts.peakHours) {
        this.charts.peakHours.destroy();
      }

      // Generate hourly data (0-23 hours)
      const hours = Array.from({length: 24}, (_, i) => i);
      const labels = hours.map(h => h + ':00');
      
      // Sample data - in real app, this would come from backend
      const peakData = this.analytics.peak_hours?.length > 0 
        ? this.analytics.peak_hours 
        : hours.map(h => {
            // Simulate peak hours: higher activity 8am-6pm
            if (h >= 8 && h <= 18) {
              return Math.floor(Math.random() * 5) + 2;
            }
            return Math.floor(Math.random() * 2);
          });

      this.charts.peakHours = new ChartJS(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: '# Vehicles Parked',
            data: peakData,
            borderColor: '#2196f3',
            backgroundColor: 'rgba(33, 150, 243, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#2196f3',
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 3
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: 'index'
          },
          plugins: {
            legend: {
              display: true,
              position: 'top',
              labels: {
                font: { size: 12 },
                color: '#666'
              }
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: '#2196f3',
              borderWidth: 1,
              cornerRadius: 8
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: {
                color: '#666',
                font: { size: 10 },
                maxRotation: 45,
                minRotation: 45
              }
            },
            y: {
              beginAtZero: true,
              grid: { color: 'rgba(0, 0, 0, 0.1)' },
              ticks: {
                color: '#666',
                font: { size: 12 },
                stepSize: 1
              }
            }
          }
        }
      });
    },

    createDurationChart() {
      const ctx = this.$refs.durationChart?.getContext('2d');
      if (!ctx) return;

      if (this.charts.duration) {
        this.charts.duration.destroy();
      }

      const labels = ['<1 hour', '1-2 hours', '2-4 hours', '4-8 hours', '8+ hours'];
      
      // Sample data - in real app, this would come from backend
      const durationData = this.analytics.duration_distribution?.length > 0
        ? this.analytics.duration_distribution
        : [5, 12, 8, 3, 1]; // Sample distribution

      this.charts.duration = new ChartJS(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Number of Vehicles',
            data: durationData,
            backgroundColor: 'rgba(156, 39, 176, 0.7)',
            borderColor: 'rgba(156, 39, 176, 1)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#fff',
              bodyColor: '#fff',
              borderColor: '#9c27b0',
              borderWidth: 1,
              cornerRadius: 8,
              displayColors: false
            }
          },
          scales: {
            x: {
              grid: { display: false },
              ticks: {
                color: '#666',
                font: { size: 12 }
              }
            },
            y: {
              beginAtZero: true,
              grid: { color: 'rgba(0, 0, 0, 0.1)' },
              ticks: {
                color: '#666',
                font: { size: 12 },
                stepSize: 1,
                callback: function(value) {
                  return Math.floor(value);
                }
              }
            }
          }
        }
      });
    },

    createStatusChart() {
      const ctx = this.$refs.statusChart?.getContext('2d');
      if (!ctx) return;

      if (this.charts.status) {
        this.charts.status.destroy();
      }

      const labels = ['Pending', 'Confirmed', 'Parked', 'Parked Out', 'Cancelled/Rejected'];
      
      // Sample data - in real app, this would come from backend
      const statusData = this.analytics.status_distribution?.length > 0
        ? this.analytics.status_distribution
        : [2, 5, 8, 12, 3]; // Sample distribution

      this.charts.status = new ChartJS(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: statusData,
            backgroundColor: [
              'rgba(255, 193, 7, 0.8)',   // Amber - Pending
              'rgba(76, 175, 80, 0.8)',   // Green - Confirmed
              'rgba(33, 150, 243, 0.8)',  // Blue - Parked
              'rgba(158, 158, 158, 0.8)', // Grey - Parked Out
              'rgba(244, 67, 54, 0.8)'    // Red - Cancelled
            ],
            borderColor: '#fff',
            borderWidth: 3,
            hoverBackgroundColor: [
              'rgba(255, 193, 7, 1)',
              'rgba(76, 175, 80, 1)',
              'rgba(33, 150, 243, 1)',
              'rgba(158, 158, 158, 1)',
              'rgba(244, 67, 54, 1)'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 10,
                font: { size: 11 },
                color: '#666'
              }
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#fff',
              bodyColor: '#fff',
              cornerRadius: 8,
              callbacks: {
                label: function(context) {
                  const total = context.dataset.data.reduce((a, b) => a + b, 0);
                  const percentage = ((context.parsed / total) * 100).toFixed(1);
                  return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                }
              }
            }
          }
        }
      });
    },

    // Cleanup method for destroying charts
    destroyCharts() {
      Object.values(this.charts).forEach(chart => {
        if (chart) {
          chart.destroy();
        }
      });
      this.charts = {
        revenue: null,
        utilization: null,
        activity: null,
        overallUtilization: null,
        peakHours: null,
        duration: null,
        status: null
      };
    },

    // --- Parking Visualization Methods ---
    async fetchVisualizationData() {
      this.visualizationLoading = true;
      this.visualizationError = null;

      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/parking_lots/visualization', {
          headers: { 'auth-token': token }
        });

        if (response.ok) {
          this.visualizationData = await response.json();
        } else {
          this.visualizationError = 'Failed to fetch parking lot visualization data';
          this.visualizationData = [];
        }
      } catch (err) {
        console.error('Error fetching visualization data:', err);
        this.visualizationError = 'Error loading parking lot visualization';
        this.visualizationData = [];
      } finally {
        this.visualizationLoading = false;
      }
    },

    handleLotMenu(lot) {
      // Handle lot menu actions (edit, delete, etc.)
      this.editLot(lot);
    },

    // --- Task Management Methods ---
    async triggerTask(taskName) {
      this.taskStatus[taskName] = 'running';
      this.taskResults[taskName] = null;
      
      // Show "running" toast
      this.$toast.info(`Task '${this.getTaskTitle(taskName)}' has started.`);

      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch(`http://localhost:5000/api/admin/tasks/trigger/${taskName}`, {
          method: 'POST',
          headers: {
            'auth-token': token,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const result = await response.json();
          
          // Format detailed result message
          let detailedMessage = this.formatDetailedTaskResult(taskName, result);
          this.taskResults[taskName] = detailedMessage;
          this.taskStatus[taskName] = 'completed';
          
          // Add to task logs
          this.addTaskLog(taskName, 'success', detailedMessage, result);
          
          // Show success toast with result details
          this.$toast.success(`Task '${this.getTaskTitle(taskName)}' completed successfully.`);
          
          // Handle PDF download if applicable
          if (taskName === 'download_csv_report') {
            const downloadPath = result.file_path || result.download_url || result.filename;
            if (downloadPath) {
              // Small delay to ensure file is written to disk
              setTimeout(() => {
                this.downloadFile(downloadPath);
                this.$toast.success('PDF report downloaded successfully.');
              }, 500);
            } else {
              console.warn('No download path found in result:', result);
            }
          }
          
          // Auto-clear result after 10 seconds
          setTimeout(() => {
            this.taskResults[taskName] = null;
            this.taskStatus[taskName] = 'idle';
          }, 10000);
        } else {
          const errorData = await response.json();
          this.taskResults[taskName] = `Error: ${errorData.error || 'Task failed'}`;
          this.taskStatus[taskName] = 'error';
          
          // Show error toast
          this.$toast.error(`Task '${this.getTaskTitle(taskName)}' failed: ${errorData.error}`);
        }
      } catch (err) {
        console.error(`Error triggering task ${taskName}:`, err);
        this.taskResults[taskName] = `Error: ${err.message}`;
        this.taskStatus[taskName] = 'error';
        
        // Show error toast
        this.$toast.error(`Task '${this.getTaskTitle(taskName)}' failed with a network error.`);
      }
    },
    
    getTaskTitle(taskName) {
      const task = this.taskCatalog.find(t => t.key === taskName);
      return task ? task.title : taskName;
    },
    
    downloadFile(filePath) {
      if (!filePath) {
        console.error('No file path provided for download');
        return;
      }

      // Handle different path formats
      let href;
      const isAbsoluteUrl = /^https?:\/\//i.test(filePath);
      
      if (isAbsoluteUrl) {
        href = filePath;
      } else {
        // Normalize path - ensure it starts with /
        const normalizedPath = filePath.startsWith('/') ? filePath : `/${filePath}`;
        // Use backend URL (port 5000) for static files
        const backendUrl = 'http://localhost:5000';
        href = `${backendUrl}${normalizedPath}`;
      }

      console.log('Downloading file from:', href);

      // Create download link
      const link = document.createElement('a');
      link.href = href;
      link.download = href.split('/').pop();
      link.target = '_blank'; // Open in new tab as fallback
      document.body.appendChild(link);
      link.click();
      
      // Clean up after a short delay
      setTimeout(() => {
        document.body.removeChild(link);
      }, 100);
    },
    
    addTaskLog(taskName, status, message, details = {}) {
      this.taskLogs.unshift({
        id: Date.now(),
        taskName: this.getTaskTitle(taskName),
        status,
        message,
        details,
        timestamp: new Date().toLocaleString()
      });
      
      // Keep only last 50 logs
      if (this.taskLogs.length > 50) {
        this.taskLogs = this.taskLogs.slice(0, 50);
      }

      this.saveTaskLogs();
    },
    
    shouldShowTaskResult(taskName) {
      if (!this.taskResults[taskName]) {
        return false;
      }

      const suppressedTasks = [
        'cleanup_old_csv_files',
        'system_health_check',
        'auto_release_expired_reservations',
        'daily_update'
      ];

      return !suppressedTasks.includes(taskName);
    },
    loadTaskLogs() {
      try {
        const stored = localStorage.getItem('admin-task-logs');
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) {
            this.taskLogs = parsed;
          }
        }
      } catch (err) {
        console.warn('Failed to load task logs from storage', err);
      }
    },
    saveTaskLogs() {
      try {
        const logsToPersist = this.taskLogs.slice(0, 50);
        localStorage.setItem('admin-task-logs', JSON.stringify(logsToPersist));
      } catch (err) {
        console.warn('Failed to persist task logs', err);
      }
    },
    
    formatDetailedTaskResult(taskName, result) {
      if (taskName === 'system_health_check') {
        const parts = [];
        if (result.overview) {
          parts.push(`Active Reservations: ${result.overview.active_reservations || 0}`);
          parts.push(`Total Spots: ${result.overview.total_spots || 0}`);
          parts.push(`Utilization: ${result.utilization_percent || 0}%`);
        }
        if (result.issues && result.issues.length > 0) {
          parts.push(`⚠️ Issues Found: ${result.issues.length}`);
        } else {
          parts.push('✅ All systems healthy');
        }
        return parts.join(' | ');
      }
      
      if (taskName === 'cleanup_old_csv_files') {
        return `${result.message || 'Cleanup completed'} | Files removed: ${result.deleted_count || 0}`;
      }
      
      if (taskName === 'auto_release_expired_reservations') {
        return `${result.message || 'Release completed'} | Spots released: ${result.released_count || 0}`;
      }
      
      return result.message || 'Task completed successfully';
    },
    
    async fetchTaskLogs() {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/tasks/logs?limit=50', {
          headers: { 'auth-token': token }
        });
        
        if (response.ok) {
          const data = await response.json();
          // Merge with existing logs, avoiding duplicates
          const existingIds = new Set(this.taskLogs.map(log => log.id));
          const newLogs = data.logs.filter(log => !existingIds.has(log.id));
          this.taskLogs = [...newLogs, ...this.taskLogs].slice(0, 50);
        }
      } catch (err) {
        console.error('Error fetching task logs:', err);
      }
    },

    getTabTitle() {
      const titles = {
        'lots': 'Manage Parking Lots',
        'visualization': 'Bird\'s Eye View',
        'users': 'Manage Users',
        'reservations': 'Manage Reservations',
        'analytics': 'Summaries',
        'tasks': 'Task Management'
      };
      return titles[this.activeTab] || 'Dashboard';
    },
    
    // Data Consistency Methods
    async checkDataConsistency() {
      this.consistencyStatus = 'checking';
      this.consistencyResult = null;
      this.consistencyIssues = [];
      this.consistencyFixesApplied = [];
      
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/data/consistency-check', {
          headers: { 'auth-token': token }
        });
        
        if (response.ok) {
          const data = await response.json();
          this.consistencyResult = data;
          this.consistencyIssues = data.issues || [];
          this.$toast.success(data.message || `Found ${data.total_issues} issues`);
        } else {
          this.$toast.error('Failed to check consistency');
        }
      } catch (err) {
        console.error('Error checking consistency:', err);
        this.$toast.error('Error checking consistency');
      } finally {
        this.consistencyStatus = 'idle';
      }
    },
    
    async fixDataConsistency() {
      this.consistencyStatus = 'fixing';
      
      try {
        const token = localStorage.getItem('auth-token');
        const response = await fetch('http://localhost:5000/api/admin/data/consistency-check', {
          method: 'POST',
          headers: { 'auth-token': token }
        });
        
        if (response.ok) {
          const data = await response.json();
          this.consistencyFixesApplied = data.fixes_applied || [];
          this.consistencyIssues = data.issues || [];
          this.$toast.success(data.message || `Applied ${data.fixes_applied.length} fixes`);
          
          // Refresh data
          await this.fetchLots();
          await this.fetchAnalytics();
        } else {
          this.$toast.error('Failed to fix consistency issues');
        }
      } catch (err) {
        console.error('Error fixing consistency:', err);
        this.$toast.error('Error fixing consistency issues');
      } finally {
        this.consistencyStatus = 'idle';
      }
    }
  }
};
</script>

<style scoped>
@import '@/assets/styles/AdminDashboard.css';

.tab-content-detail {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px; /* Space for scrollbar */
}

/* NUCLEAR OPTION: Force all parking lot card elements to show full content */
div[class*="lot-card"],
div[class*="lot-card-body"],
div[class*="lot-info"] {
  height: auto !important;
  max-height: none !important;
  min-height: 0 !important;
  overflow: visible !important;
}

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
.reservations-table .id-link {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  padding: 0;
  font-weight: bold;
}
.reservations-table .id-link:hover {
  text-decoration: underline;
}

.user-id-link {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  padding: 0;
  font-weight: bold;
}

.user-id-link:hover {
  text-decoration: underline;
}
</style>
