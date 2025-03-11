// Date picker initialization and validation
document.addEventListener('DOMContentLoaded', function() {
    // Initialize date inputs
    const checkInDate = document.querySelector('#check_in');
    const checkOutDate = document.querySelector('#check_out');
    const bookingForm = document.querySelector('#booking-form');
    const availabilityMessage = document.querySelector('#availability-message');
    const totalPriceElement = document.querySelector('#total-price');
    const bookButton = document.querySelector('#book-button');

    if (checkInDate && checkOutDate) {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        checkInDate.min = today;

        checkInDate.addEventListener('change', function() {
            // Set minimum check-out date to check-in date
            checkOutDate.min = checkInDate.value;

            // Clear check-out date if it's before check-in date
            if (checkOutDate.value && checkOutDate.value < checkInDate.value) {
                checkOutDate.value = '';
            }

            if (checkOutDate.value) {
                checkAvailability();
            }
        });

        checkOutDate.addEventListener('change', function() {
            if (checkInDate.value) {
                checkAvailability();
            }
        });
    }

    // Function to check room availability
    function checkAvailability() {
        const roomId = bookingForm?.dataset.roomId;
        if (!roomId || !checkInDate.value || !checkOutDate.value) return;

        const formData = new FormData();
        formData.append('check_in', checkInDate.value);
        formData.append('check_out', checkOutDate.value);
        formData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);

        fetch(`/booking/check_availability/${roomId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (availabilityMessage) {
                availabilityMessage.style.display = 'block';
                availabilityMessage.textContent = data.message;
                availabilityMessage.className = `alert alert-${data.available ? 'success' : 'danger'}`;
            }
            if (totalPriceElement) {
                totalPriceElement.textContent = `$${data.total_price}`;
            }
            if (bookButton) {
                bookButton.disabled = !data.available;
            }
        })
        .catch(error => {
            console.error('Error checking availability:', error);
            if (availabilityMessage) {
                availabilityMessage.style.display = 'block';
                availabilityMessage.textContent = 'Error checking availability. Please try again.';
                availabilityMessage.className = 'alert alert-danger';
            }
            if (bookButton) {
                bookButton.disabled = true;
            }
        });
    }

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});

// Admin dashboard charts (if needed)
function initializeCharts() {
    if (document.getElementById('bookingsChart')) {
        const ctx = document.getElementById('bookingsChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Bookings',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}