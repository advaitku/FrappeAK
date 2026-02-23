/**
 * Guest page form handler for AK Document Designer.
 *
 * Handles form validation, submission, and Accept/Decline actions
 * on the shared document page.
 */
(function () {
    "use strict";

    const config = window.AK_DOCUMENT || {};

    if (config.isLocked) {
        disableAllFields();
        return;
    }

    // Bind action buttons
    document.querySelectorAll(".ak-accept-btn, .ak-decline-btn, .ak-submit-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            const action = this.getAttribute("data-action");
            submitForm(action);
        });
    });

    function disableAllFields() {
        document.querySelectorAll(".ak-field-input").forEach((el) => {
            el.disabled = true;
        });
        document.querySelectorAll(".ak-accept-btn, .ak-decline-btn, .ak-submit-btn").forEach((btn) => {
            btn.disabled = true;
            btn.style.opacity = "0.5";
        });
    }

    function collectFieldValues() {
        const values = {};
        document.querySelectorAll("[data-fieldname]").forEach((wrapper) => {
            const fieldname = wrapper.getAttribute("data-fieldname");
            const editable = wrapper.getAttribute("data-editable") === "1";
            if (!editable) return;

            const input = wrapper.querySelector("input, textarea, select");
            if (!input) return;

            if (input.type === "checkbox") {
                values[fieldname] = input.checked ? 1 : 0;
            } else {
                values[fieldname] = input.value;
            }
        });
        return values;
    }

    function validateMandatory() {
        let valid = true;
        document.querySelectorAll("[data-mandatory='1'][data-editable='1']").forEach((wrapper) => {
            const input = wrapper.querySelector("input, textarea, select");
            if (!input) return;

            const fieldname = wrapper.getAttribute("data-fieldname");
            const value = input.type === "checkbox" ? input.checked : input.value;

            // Remove previous error styling
            wrapper.classList.remove("ak-field-error");

            if (!value && value !== 0) {
                wrapper.classList.add("ak-field-error");
                valid = false;
            }
        });
        return valid;
    }

    function submitForm(responseType) {
        if (!validateMandatory()) {
            showMessage("Please fill in all required fields.", "error");
            return;
        }

        const fieldValues = collectFieldValues();
        const submitBtn = document.querySelector("[data-action='" + responseType + "']");
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "Submitting...";
        }

        fetch("/api/method/frappe_ak.doc_api.submit_response", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Frappe-CSRF-Token": getCSRFToken(),
            },
            body: JSON.stringify({
                secret_key: config.secretKey,
                response_type: responseType,
                field_values: JSON.stringify(fieldValues),
            }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.message && data.message.success) {
                    showSuccessPage(data.message.message);
                } else if (data.exc) {
                    const errMsg = data._server_messages
                        ? JSON.parse(JSON.parse(data._server_messages)[0]).message
                        : "An error occurred. Please try again.";
                    showMessage(errMsg, "error");
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = responseType === "Accepted" ? "Accept" : responseType === "Declined" ? "Decline" : "Submit";
                    }
                }
            })
            .catch(() => {
                showMessage("Network error. Please check your connection and try again.", "error");
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = responseType;
                }
            });
    }

    function showSuccessPage(message) {
        const form = document.getElementById("ak-document-form");
        if (form) {
            form.innerHTML =
                '<div class="ak-success-message">' +
                '<div class="ak-success-icon">&#10003;</div>' +
                "<h2>" + escapeHtml(message) + "</h2>" +
                "</div>";
        }
    }

    function showMessage(text, type) {
        // Remove existing messages
        document.querySelectorAll(".ak-toast").forEach((el) => el.remove());

        const toast = document.createElement("div");
        toast.className = "ak-toast ak-toast-" + type;
        toast.textContent = text;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 5000);
    }

    function getCSRFToken() {
        // 1. Frappe's auto-injected global (most reliable for guest pages)
        if (window.frappe && window.frappe.csrf_token) return window.frappe.csrf_token;
        // 2. Our config object
        if (config.csrfToken) return config.csrfToken;
        // 3. Meta tag
        const meta = document.querySelector('meta[name="csrf_token"]');
        if (meta && meta.getAttribute("content")) return meta.getAttribute("content");
        // 4. Cookie fallback
        const match = document.cookie.match(/csrf_token=([^;]+)/);
        return match ? match[1] : "None";
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
})();
