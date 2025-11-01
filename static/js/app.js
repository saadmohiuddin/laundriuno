// API endpoint base URL
const API_BASE = '/api';

// Load all data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    // Auto-refresh every 30 seconds
    setInterval(loadData, 30000);
});

// Main function to load all data
async function loadData() {
    await Promise.all([
        loadMachines(),
        loadBestTimes(),
        loadAvailability(),
        loadStatistics()
    ]);
    updateLastUpdateTime();
}

// Load machine status
async function loadMachines() {
    try {
        const response = await fetch(`${API_BASE}/machines`);
        const machines = await response.json();
        
        // Update available count
        const availableCount = machines.filter(m => !m.is_running).length;
        document.getElementById('available-count').innerHTML = `
            <span class="stat-number">${availableCount}</span>
            <span class="stat-label">machines available</span>
        `;
        
        // Update machines grid
        const grid = document.getElementById('machines-grid');
        if (machines.length === 0) {
            grid.innerHTML = '<p>No machines found.</p>';
            return;
        }
        
        grid.innerHTML = machines.map(machine => {
            const statusClass = machine.is_running ? 'in-use' : 'available';
            const statusText = machine.is_running ? 'In Use' : 'Available';
            const statusBadgeClass = machine.is_running ? 'status-in-use' : 'status-available';
            
            return `
                <div class="machine-card ${statusClass}">
                    <div class="machine-name">${machine.name}</div>
                    <div class="machine-status ${statusBadgeClass}">${statusText}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading machines:', error);
        document.getElementById('machines-grid').innerHTML = '<p>Error loading machine status.</p>';
    }
}

// Load best times recommendation
async function loadBestTimes() {
    try {
        const response = await fetch(`${API_BASE}/best-times?days=7`);
        const data = await response.json();
        
        const container = document.getElementById('best-times');
        
        if (data.recommended_times && data.recommended_times.length > 0) {
            container.innerHTML = data.recommended_times.map(time => `
                <div class="time-card">
                    <div class="time-range">${time.time_range}</div>
                    <div class="usage-count">${time.usage_count} uses</div>
                </div>
            `).join('');
            
            if (data.message) {
                container.innerHTML += `<div class="message-box">${data.message}</div>`;
            }
        } else {
            container.innerHTML = `<div class="message-box">${data.message || 'No data available yet.'}</div>`;
        }
    } catch (error) {
        console.error('Error loading best times:', error);
        document.getElementById('best-times').innerHTML = '<p>Error loading recommendations.</p>';
    }
}

// Load availability forecast
async function loadAvailability() {
    try {
        const response = await fetch(`${API_BASE}/availability?days=7`);
        const availability = await response.json();
        
        const container = document.getElementById('availability-chart');
        
        if (availability.length === 0) {
            container.innerHTML = '<p>No availability data yet.</p>';
            return;
        }
        
        const maxMachines = Math.max(...availability.map(a => a.avg_available + a.avg_in_use));
        
        container.innerHTML = availability.map(item => {
            const percentage = maxMachines > 0 ? (item.avg_available / maxMachines * 100) : 0;
            return `
                <div class="availability-bar">
                    <div class="hour-label">${item.time_range}</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: ${percentage}%"></div>
                    </div>
                    <div class="bar-label">${item.avg_available.toFixed(1)} avg available</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading availability:', error);
        document.getElementById('availability-chart').innerHTML = '<p>Error loading availability forecast.</p>';
    }
}

// Load usage statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/statistics?days=7`);
        const stats = await response.json();
        
        const container = document.getElementById('statistics');
        
        const statCards = [
            {
                title: 'Total Sessions',
                value: stats.total_sessions
            },
            {
                title: 'Average Duration',
                value: formatDuration(stats.average_duration)
            },
            {
                title: 'Total Usage Time',
                value: formatDuration(stats.total_usage_time)
            }
        ];
        
        container.innerHTML = statCards.map(card => `
            <div class="stat-card">
                <h3>${card.title}</h3>
                <div class="value">${card.value}</div>
            </div>
        `).join('');
        
        // Add busiest hours if available
        if (stats.busiest_hours && stats.busiest_hours.length > 0) {
            const busiestHtml = `
                <div class="stat-card">
                    <h3>Busiest Hours</h3>
                    <div class="value" style="font-size: 1.5em;">
                        ${stats.busiest_hours.map(h => `${h.hour}:00 (${h.count})`).join('<br>')}
                    </div>
                </div>
            `;
            container.innerHTML += busiestHtml;
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
        document.getElementById('statistics').innerHTML = '<p>Error loading statistics.</p>';
    }
}

// Helper function to format duration
function formatDuration(seconds) {
    // Handle edge cases
    if (seconds < 0) return '0m';
    if (seconds === 0) return '0m';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}

// Update last update time
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    document.getElementById('last-update').textContent = timeString;
}
