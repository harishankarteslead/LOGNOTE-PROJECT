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

            const usernameErr = document.getElementById("username-error");
            const passwordErr = document.getElementById("password-error");

            if (usernameErr) usernameErr.innerText = "";
            if (passwordErr) passwordErr.innerText = "";

            // Check if username is empty
            if (username === "") {
                if (usernameErr) usernameErr.innerText = "Please enter your username.";
                if (usernameInput) usernameInput.focus();
                event.preventDefault();
                return;
            }

            // Check if password is empty
            if (password === "") {
                if (passwordErr) passwordErr.innerText = "Please enter your password.";
                if (passwordInput) passwordInput.focus();
                event.preventDefault();
                return;
            }
        });
    }
});

