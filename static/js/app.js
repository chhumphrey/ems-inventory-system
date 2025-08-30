// EMS Inventory Management System - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide only flash messages (not dashboard alerts) after 5 seconds
    setTimeout(function() {
        var flashAlerts = document.querySelectorAll('.alert:not(.dashboard-alert)');
        flashAlerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Ensure dashboard alerts are never hidden
    var dashboardAlerts = document.querySelectorAll('.dashboard-alert');
    dashboardAlerts.forEach(function(alert) {
        // Remove any Bootstrap auto-hide classes
        alert.classList.remove('fade', 'show');
        
        // Prevent Bootstrap from hiding this alert
        if (alert.dataset.bsAlert) {
            delete alert.dataset.bsAlert;
        }
        
        // Override any Bootstrap alert methods for dashboard alerts
        if (alert._bsAlert) {
            alert._bsAlert._config.autohide = false;
        }
    });

    // Form validation enhancements
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Quantity input validation
    var quantityInputs = document.querySelectorAll('input[name^="quantity_"]');
    quantityInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var value = parseInt(this.value);
            if (value < 0) {
                this.value = 0;
            }
        });
    });

    // Date input validation
    var dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            var selectedDate = new Date(this.value);
            var today = new Date();
            
            if (selectedDate < today) {
                this.classList.add('is-invalid');
                if (!this.nextElementSibling || !this.nextElementSibling.classList.contains('invalid-feedback')) {
                    var feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Date cannot be in the past';
                    this.parentNode.appendChild(feedback);
                }
            } else {
                this.classList.remove('is-invalid');
                var feedback = this.parentNode.querySelector('.invalid-feedback');
                if (feedback) {
                    feedback.remove();
                }
            }
        });
    });

    // Search functionality
    var searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            var searchTerm = this.value.toLowerCase();
            var tableRows = document.querySelectorAll('tbody tr');
            
            tableRows.forEach(function(row) {
                var text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Auto-save form data
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        var formId = form.id || 'form_' + Math.random().toString(36).substr(2, 9);
        form.id = formId;
        
        // Save form data to localStorage
        form.addEventListener('input', function() {
            var formData = new FormData(form);
            var data = {};
            for (var [key, value] of formData.entries()) {
                data[key] = value;
            }
            localStorage.setItem('form_' + formId, JSON.stringify(data));
        });
        
        // Restore form data from localStorage
        var savedData = localStorage.getItem('form_' + formId);
        if (savedData) {
            try {
                var data = JSON.parse(savedData);
                for (var key in data) {
                    var input = form.querySelector('[name="' + key + '"]');
                    if (input) {
                        input.value = data[key];
                    }
                }
            } catch (e) {
                console.error('Error restoring form data:', e);
            }
        }
        
        // Clear saved data on successful submit
        form.addEventListener('submit', function() {
            localStorage.removeItem('form_' + formId);
        });
    });

    // Real-time inventory calculations
    var inventoryForms = document.querySelectorAll('#inventoryForm');
    inventoryForms.forEach(function(form) {
        var totalItems = 0;
        var quantityInputs = form.querySelectorAll('input[name^="quantity_"]');
        
        quantityInputs.forEach(function(input) {
            input.addEventListener('input', function() {
                updateInventoryTotal();
            });
        });
        
        function updateInventoryTotal() {
            totalItems = 0;
            quantityInputs.forEach(function(input) {
                totalItems += parseInt(input.value) || 0;
            });
            
            // Update display if there's a total counter
            var totalDisplay = document.getElementById('inventory-total');
            if (totalDisplay) {
                totalDisplay.textContent = totalItems;
            }
        }
    });

    // Responsive table handling
    function handleResponsiveTables() {
        var tables = document.querySelectorAll('.table-responsive');
        tables.forEach(function(table) {
            var isOverflowing = table.scrollWidth > table.clientWidth;
            if (isOverflowing) {
                table.classList.add('has-overflow');
            }
        });
    }
    
    handleResponsiveTables();
    window.addEventListener('resize', handleResponsiveTables);

    // Print functionality
    var printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Export functionality (placeholder for future CSV export)
    var exportButtons = document.querySelectorAll('.btn-export');
    exportButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            alert('Export functionality will be implemented in a future update.');
        });
    });
});

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    var date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    var date = new Date(dateString);
    return date.toLocaleString();
}

function showNotification(message, type = 'info') {
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    var container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        var bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}
