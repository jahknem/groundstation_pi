document.addEventListener('DOMContentLoaded', () => {
    let socket = io.connect('http://localhost:8000');
    let mapping = {};

    // Handle gamepad connection
    window.addEventListener("gamepadconnected", (event) => {
        const gamepad = event.gamepad;
        console.log(`Gamepad connected: ${gamepad.id}`);
        initializeMappingUI(gamepad);
        updateGamepad(gamepad);
    });

    // Initialize mapping UI
    function initializeMappingUI(gamepad) {
        const form = document.getElementById('mapping-form');
        // Generate mapping inputs for buttons
        gamepad.buttons.forEach((button, index) => {
            const label = document.createElement('label');
            label.textContent = `Button ${index}: `;
            const input = document.createElement('input');
            input.type = 'text';
            input.name = `button_${index}`;
            label.appendChild(input);
            form.appendChild(label);
            form.appendChild(document.createElement('br'));
        });
        // Generate mapping inputs for axes
        gamepad.axes.forEach((axis, index) => {
            const label = document.createElement('label');
            label.textContent = `Axis ${index}: `;
            const input = document.createElement('input');
            input.type = 'text';
            input.name = `axis_${index}`;
            label.appendChild(input);
            form.appendChild(label);
            form.appendChild(document.createElement('br'));
        });
        // Submit button
        const submit = document.createElement('button');
        submit.textContent = 'Save Mapping';
        submit.type = 'button';
        submit.onclick = saveMapping;
        form.appendChild(submit);
    }

    // Save mapping
    function saveMapping() {
        const formData = new FormData(document.getElementById('mapping-form'));
        mapping = {};
        for (let [key, value] of formData.entries()) {
            if (value.trim() !== '') {
                mapping[key] = value.trim();
            }
        }
        // Send mapping to backend
        axios.post('/save-mapping', mapping)
            .then(response => {
                alert('Mapping saved successfully!');
            })
            .catch(error => {
                console.error('Error saving mapping:', error);
            });
    }

    // Update gamepad inputs
    function updateGamepad(gamepad) {
        const animate = () => {
            const gp = navigator.getGamepads()[gamepad.index];
            if (!gp) return;

            // Update controller animation based on gp.buttons and gp.axes

            // Prepare mapped input data
            const buttons = {};
            gp.buttons.forEach((button, index) => {
                const key = `button_${index}`;
                const action = mapping[key] || key;
                buttons[action] = button.pressed;
            });
            const axes = {};
            gp.axes.forEach((axis, index) => {
                const key = `axis_${index}`;
                const action = mapping[key] || key;
                axes[action] = axis;
            });

            // Send data to backend via WebSocket
            socket.emit('gamepad_input', { buttons, axes });

            requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
    }
});
