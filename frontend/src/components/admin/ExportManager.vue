<template>
    <div class="export-manager">
        <div class="export-section">
            <h3>📊 Export Data</h3>

            <!-- CSV Export -->
            <div class="export-card">
                <h4>CSV Report</h4>
                <p>Export all reservation data to CSV format</p>
                <button @click="exportCSV" :disabled="csvExporting" class="btn btn-primary">
                    {{ csvExporting ? 'Generating...' : 'Export CSV' }}
                </button>

                <!-- CSV Status -->
                <div v-if="csvTaskId" class="task-status">
                    <div class="status-indicator" :class="csvStatus">
                        {{ csvStatusText }}
                    </div>
                    <div v-if="csvStatus === 'completed'" class="download-section">
                        <a :href="csvDownloadUrl" class="btn btn-success" download>
                            📥 Download CSV
                        </a>
                    </div>
                </div>
            </div>

            <!-- Monthly Report -->
            <div class="export-card">
                <h4>Monthly Report</h4>
                <p>Generate and email monthly analytics</p>
                <button @click="sendMonthlyReport" :disabled="reportSending" class="btn btn-secondary">
                    {{ reportSending ? 'Generating...' : 'Send Monthly Report' }}
                </button>

                <!-- Report Status -->
                <div v-if="reportTaskId" class="task-status">
                    <div class="status-indicator" :class="reportStatus">
                        {{ reportStatusText }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ExportManager',
    data() {
        return {
            // CSV Export
            csvTaskId: null,
            csvStatus: null,
            csvExporting: false,
            csvDownloadUrl: null,

            // Monthly Report
            reportTaskId: null,
            reportStatus: null,
            reportSending: false,

            // Polling intervals
            csvInterval: null,
            reportInterval: null
        }
    },

    computed: {
        csvStatusText() {
            switch (this.csvStatus) {
                case 'pending': return 'Generating CSV...';
                case 'completed': return 'CSV Ready for Download';
                case 'failed': return 'CSV Generation Failed';
                default: return '';
            }
        },

        reportStatusText() {
            switch (this.reportStatus) {
                case 'pending': return 'Generating Report...';
                case 'completed': return 'Report Sent Successfully';
                case 'failed': return 'Report Generation Failed';
                default: return '';
            }
        }
    },

    methods: {
        async exportCSV() {
            try {
                this.csvExporting = true;

                const response = await fetch('/user/export', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${this.$store.state.auth.token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error('Export request failed');
                }

                const data = await response.json();
                this.csvTaskId = data.task_id;
                this.csvStatus = 'pending';

                // Start polling for status
                this.pollCSVStatus();

            } catch (error) {
                console.error('CSV Export Error:', error);
                this.$toast.error('Failed to start CSV export');
            } finally {
                this.csvExporting = false;
            }
        },

        async pollCSVStatus() {
            if (!this.csvTaskId) return;

            this.csvInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/user/export/status/${this.csvTaskId}`, {
                        headers: {
                            'Authorization': `Bearer ${this.$store.state.auth.token}`
                        }
                    });

                    const data = await response.json();
                    this.csvStatus = data.status;

                    if (data.status === 'completed') {
                        this.csvDownloadUrl = data.download_url;
                        clearInterval(this.csvInterval);
                        this.$toast.success('CSV export completed!');
                    } else if (data.status === 'failed') {
                        clearInterval(this.csvInterval);
                        this.$toast.error('CSV export failed: ' + data.error);
                    }

                } catch (error) {
                    console.error('Status check error:', error);
                    clearInterval(this.csvInterval);
                }
            }, 2000); // Check every 2 seconds
        },

        async sendMonthlyReport() {
            try {
                this.reportSending = true;

                const response = await fetch('/user/mail', {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${this.$store.state.auth.token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error('Report request failed');
                }

                const data = await response.json();
                this.reportTaskId = data.task_id;
                this.reportStatus = 'pending';

                // Start polling for status
                this.pollReportStatus();

            } catch (error) {
                console.error('Monthly Report Error:', error);
                this.$toast.error('Failed to start monthly report');
            } finally {
                this.reportSending = false;
            }
        },

        async pollReportStatus() {
            if (!this.reportTaskId) return;

            this.reportInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/user/mail/status/${this.reportTaskId}`, {
                        headers: {
                            'Authorization': `Bearer ${this.$store.state.auth.token}`
                        }
                    });

                    const data = await response.json();
                    this.reportStatus = data.status;

                    if (data.status === 'completed') {
                        clearInterval(this.reportInterval);
                        this.$toast.success('Monthly report sent successfully!');
                    } else if (data.status === 'failed') {
                        clearInterval(this.reportInterval);
                        this.$toast.error('Monthly report failed: ' + data.error);
                    }

                } catch (error) {
                    console.error('Report status check error:', error);
                    clearInterval(this.reportInterval);
                }
            }, 3000); // Check every 3 seconds
        }
    },

    beforeUnmount() {
        // Clean up intervals
        if (this.csvInterval) clearInterval(this.csvInterval);
        if (this.reportInterval) clearInterval(this.reportInterval);
    }
}
</script>

<style scoped>
.export-manager {
    padding: 20px;
}

.export-section {
    max-width: 800px;
}

.export-card {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.export-card h4 {
    margin-top: 0;
    color: #333;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    text-decoration: none;
    display: inline-block;
}

.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.btn-primary {
    background-color: #007bff;
    color: white;
}

.btn-secondary {
    background-color: #6c757d;
    color: white;
}

.btn-success {
    background-color: #28a745;
    color: white;
}

.task-status {
    margin-top: 15px;
    padding: 10px;
    border-radius: 4px;
    background-color: #f8f9fa;
}

.status-indicator {
    font-weight: bold;
    padding: 5px 10px;
    border-radius: 4px;
    display: inline-block;
}

.status-indicator.pending {
    background-color: #ffc107;
    color: #856404;
}

.status-indicator.completed {
    background-color: #d4edda;
    color: #155724;
}

.status-indicator.failed {
    background-color: #f8d7da;
    color: #721c24;
}

.download-section {
    margin-top: 10px;
}
</style>