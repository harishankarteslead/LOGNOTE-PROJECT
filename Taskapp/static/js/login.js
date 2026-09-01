// Wait for the web page (DOM) to fully load before running our script
document.addEventListener("DOMContentLoaded", function () {

    // Get references to the form and input fields from HTML
    var loginForm = document.querySelector("form");
    var usernameInput = document.getElementById("username");
    var passwordInput = document.getElementById("password");

    // Make sure the form exists on the page before adding event listener
    if (loginForm) {

        // Listen for the submit event when user clicks the Login button
        loginForm.addEventListener("submit", function (event) {

            // Read input values and remove extra whitespace
            var username = usernameInput ? usernameInput.value.trim() : "";
            var password = passwordInput ? passwordInput.value.trim() : "";

            var usernameErr = document.getElementById("username-error");
            var passwordErr = document.getElementById("password-error");

            // Reset previous error messages
            if (usernameErr) {
                usernameErr.innerText = "";
            }
            if (passwordErr) {
                passwordErr.innerText = "";
            }

            // Check if username is empty
            if (username === "") {
                if (usernameErr) {
                    usernameErr.innerText = "Please enter your username.";
                }
                if (usernameInput) {
                    usernameInput.focus();
                }
                event.preventDefault();
                return;
            }

            // Check if password is empty
            if (password === "") {
                if (passwordErr) {
                    passwordErr.innerText = "Please enter your password.";
                }
                if (passwordInput) {
                    passwordInput.focus();
                }
                event.preventDefault();
                return;
            }
        });
    }
});


