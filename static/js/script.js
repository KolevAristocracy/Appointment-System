const API_URL = '/api';

document.addEventListener('DOMContentLoaded', async() => {
    // 1. Set MIN date to Today (Restriction 1)
    const dateInput = document.getElementById('date');
    const today = new Date().toISOString().split('T')[0];
    // const categoryInputs = document.querySelectorAll('input[name="category"]');
    dateInput.setAttribute('min', today);

    await loadCategories();

    // categoryInputs.forEach(input => {
    //     input.addEventListener('change', (e) => {
    //         const selectedCategory = e.target.value;
    //         loadServices(selectedCategory)
    //
    //         resetDropdown('service', 'Зареждане...');
    //         resetDropdown('professional', '-- Първо изберете услуга --');
    //         document.getElementById('slots-container').innerHTML = '';
    //     });
    // });

    // 2. Add Listeners to fetch slots when inputs change
    document.getElementById('service').addEventListener('change', (e) => {
        const serviceId = e.target.value;
        loadProfessionals(serviceId)

        resetDropdown('professional', '-- Избери служител --');
        document.getElementById('slots-container').innerHTML = '<p>Моля, изберете служител.</p>';
    });

    document.getElementById('date').addEventListener('change', loadAvailableSlots);
    document.getElementById('professional').addEventListener('change', loadAvailableSlots);

    // Load initial data
    loadServices('hair');
    // loadProfessionals();  // CHECK LATER: No initial info for all pro's is shown


    // Form submit listener
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleFormSubmit);
    }
});

// Helper Function
function resetDropdown(id, defaultText) {
    const select = document.getElementById(id);
    select.innerHTML = `<option value="">${defaultText}</option>`; // maybe It's a good idea later to change this
    select.value = "";
}

async function loadCategories() {
    const container = document.getElementById('category-container');

    try {
        const response = await fetch(`${API_URL}/categories/`);
        const categories = await response.json();

        container.innerHTML = '';

        if (categories.length === 0) {
            container.innerHTML = 'Няма активни бизнеси.';
            return;
        }

        categories.forEach((cat, index) => {
            // Creating Label (so the text is clickable)
            const label = document.createElement('label');
            label.style.cursor = "pointer";
            label.style.marginRight = "15px";

            // Creating Radio Input
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'category';
            radio.value = cat.slug;

            // If It's the first element it selected by default
            if (index === 0) {
                radio.checked = true;
            }

            // Adding logic on click
            radio.addEventListener('change', (e) => {
                handleCategoryChange(e.target.value);
            });

            // Adding the text (e.g. Barber)
            const span = document.createElement('span');
            span.textContent = `${cat.icon} ${cat.name}`

            // Adding input and text in the label
            label.appendChild(radio);
            label.appendChild(span);

            // Adding the label in the container
            container.appendChild(label);
        });

        // Auto start: loading the services for the first category immediately
        if (categories.length > 0) {
            handleCategoryChange(categories[0].slug);
        }
    } catch (error) {
        console.error("Грешка при зареждане на категории:", error);
        container.innerHTML = '<span class="error">Грешка при връзка със сървъра.</span>';
    }
}

function handleCategoryChange(categorySlug) {
    console.log("Избрана категория:", categorySlug);
    // Loading services for the slug
    loadServices(categorySlug);

    // Reset
    resetDropdown('service', 'Зареждане...');
    resetDropdown('professional', '-- Първо изберете услуга --');
    document.getElementById('slots-container').innerHTML = '';
}

// Function to fetch services from Django
async function loadServices(category) {
    try {
        const response = await fetch(`${API_URL}/services/?category=${category}`);
        if (!response.ok) throw new Error("Failed to fetch services");

        const services = await response.json();
        const select = document.getElementById('service');

        // Clear options except the first one
        select.innerHTML = '<option value="">-- Избери услуга --</option>';

        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.id;
            option.textContent = `${service.name} (${service.price} BGN)`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading services:', error);
    }
}

// Function to fetch professionals from Django
async function loadProfessionals(serviceId = null) {
    try {
        let url = `${API_URL}/professionals/`;
        // If a service is chosen, filter the professionals, which can do It.
        if (serviceId) {
            url += `?service=${serviceId}`;
        }
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch professionals");

        const pros = await response.json();
        const select = document.getElementById('professional');

        select.innerHTML = '<option value="">-- Избери служител --</option>';

        pros.forEach(pro => {
            const option = document.createElement('option');
            option.value = pro.id;
            option.textContent = pro.name;
            select.appendChild(option);
        });

        document.getElementById('slots-container').innerHTML = '';

    } catch (error) {
        console.error('Error loading professionals:', error);
    }
}

// Function to load available slots
async function loadAvailableSlots() {
    const professionalId = document.getElementById('professional').value;
    const dateValue = document.getElementById('date').value;
    const serviceId = document.getElementById('service').value;

    const slotsContainer = document.getElementById('slots-container');
    const timeInput = document.getElementById('time');

    // Reset current selection
    timeInput.value = '';
    slotsContainer.innerHTML = '<p>Зареждане...</p>';

    // We need both inputs to fetch data
    if (!professionalId || !dateValue || !serviceId) {
        slotsContainer.innerHTML = '';
        const pEl = document.createElement('p');
        pEl.style.color = "gray";
        pEl.textContent = "Моля, изберете Услуга, Служител и Дата.";
        slotsContainer.appendChild(pEl);
        return;
    }

    try {
        const response = await fetch(`${API_URL}/slots/?date=${dateValue}&professional=${professionalId}&service=${serviceId}`);
        const slots = await response.json();

        slotsContainer.innerHTML = '' // Clear loading text

        if (slots.error) {
            slotsContainer.innerHTML = `<p style="color: red;">Грешка: ${slots.error}</p>`;
            return;
        }

        if (slots.length === 0) {
            slotsContainer.innerHTML = ''
            const pEl = document.createElement('p');
            pEl.style.color = "red";
            pEl.textContent = "Няма свободни часове за тази дата.";
            slotsContainer.appendChild(pEl);
            return;
        }

        // Render buttons
        slots.forEach(timeStr => {
            const btn = document.createElement('button')
            btn.type = 'button'; // Important: prevent submit
            btn.className = 'time-slot';
            btn.textContent = timeStr;

            btn.onclick = function () {
                // 1. Remove 'selected' class from all others
                document.querySelectorAll('.time-slot').forEach(b => b.classList.remove('selected'));
                // 2. Add to clicked
                this.classList.add('selected');
                // 3. Set the hidden input value
                timeInput.value = this.textContent;
                //4. Hide error if visible
                document.getElementById('time-error').style.display = 'none';
            };

            slotsContainer.appendChild(btn);
        });
    } catch (error) {
        console.error('Error loading slots:', error);
        slotsContainer.innerHTML = '<p style="color: red;">Грешка при зареждане на часове.</p>';
    }
}


// Function to handle form submission
async function handleFormSubmit(event) {
    event.preventDefault(); // STOP the default form reload

    // Validation: Check if time is selected
    if (!document.getElementById('time').value) {
        document.getElementById('time-error').style.display = 'block';
        return;
    }

    // Gather data
    const formData = {
        service: document.getElementById('service').value,
        professional: document.getElementById('professional').value,
        date: document.getElementById('date').value,
        // The time now comes from our hidden input, populated by button click
        time: document.getElementById('time').value,
        client_name: document.getElementById('name').value,
        client_phone: document.getElementById('phone').value,
        client_email: document.getElementById('email').value
    };

    try {
        const response = await fetch(`${API_URL}/book/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // If you later add CSRF protection, the token goes here
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        const msgBox = document.getElementById('message');

        if (response.ok) {
            // Success Logic
            msgBox.className = 'success'; // Ensure you have this class in CSS
            msgBox.textContent = `Успешно запазено! ${result.date} в ${result.time}`;
            msgBox.style.display = 'block';
            document.getElementById('bookingForm').reset();
            document.getElementById('slots-container').innerHTML = ''; // Clear slots
        } else {
            // Error Logic (Validation errors from Django)
            console.error("Server returned errors:", result);
            msgBox.className = 'error'; // Ensure you have this class in CSS
            // Simple error formating
            msgBox.textContent = Object.values(result);
            msgBox.style.display = 'block';
        }

    } catch (error) {
        console.error('Network error during booking:', error);
        alert('Network error occurred. Please try again.');
    }
}

// Helper function to get the CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want ?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}