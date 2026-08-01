// Wait for the web page (DOM) to fully load before running our script
document.addEventListener("DOMContentLoaded", function () {

    // Get references to the form and input fields from HTML
    const loginForm = document.querySelector("form");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");

    // Make sure the form exists on the page before adding event listener
    if (loginForm) {

        // Listen for the submit event when user clicks the Login button
        loginForm.addEventListener("submit", function (event) {

            // Read input values and remove extra whitespace
            const username = usernameInput ? usernameInput.value.trim() : "";
            const password = passwordInput ? passwordInput.value.trim() : "";

            // Check if username is empty
            if (username === "") {
                alert("Please enter your username."); // Show error message to user
                if (usernameInput) usernameInput.focus(); // Move cursor to username box
                event.preventDefault(); // Stop form from submitting
                return; // Stop further execution
            }

            // Check if password is empty
            if (password === "") {
                alert("Please enter your password."); // Show error message to user
                if (passwordInput) passwordInput.focus(); // Move cursor to password box
                event.preventDefault(); // Stop form from submitting
                return; // Stop further execution
            }
        });
    }
});

