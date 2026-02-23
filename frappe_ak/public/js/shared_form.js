/**
 * Guest page form handler for AK Document Designer.
 *
 * Handles form validation, submission, and Accept/Decline actions
 * on the shared document page.
 */
(function () {
    "use strict";

    const config = window.AK_DOCUMENT || {};

    // Move action bar out of the form to body level so position:fixed works cleanly
    const actionBar = document.querySelector(".ak-action-bar");
    if (actionBar) {
        document.body.appendChild(actionBar);
    }

    // Print / Save as PDF button
    const pdfBtn = document.getElementById("ak-download-pdf");
    if (pdfBtn) {
        pdfBtn.addEventListener("click", function () {
            window.print();
        });
    }

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
            btn.style.cursor = "not-allowed";
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
                    showSuccessPage(data.message.message, responseType);
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

    function showSuccessPage(message, responseType) {
        // Hide the action bar
        const bar = document.querySelector(".ak-action-bar");
        if (bar) bar.style.display = "none";

        // Determine icon and color based on response type
        var icon, accentColor, bgColor, borderColor, typeLabel;
        if (responseType === "Accepted") {
            icon = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
            accentColor = "#16a34a";
            bgColor = "#f0fdf4";
            borderColor = "#bbf7d0";
            typeLabel = "Accepted";
        } else if (responseType === "Declined") {
            icon = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
            accentColor = "#dc2626";
            bgColor = "#fef2f2";
            borderColor = "#fecaca";
            typeLabel = "Declined";
        } else {
            icon = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
            accentColor = "#2563eb";
            bgColor = "#eff6ff";
            borderColor = "#bfdbfe";
            typeLabel = "Submitted";
        }

        var page = document.querySelector(".ak-shared-page");
        if (!page) page = document.body;

        // Replace entire page content below branding
        var form = document.getElementById("ak-document-form");
        if (form) {
            form.innerHTML =
                '<div class="ak-success-page">' +
                    '<div class="ak-success-card">' +
                        '<div class="ak-success-icon-wrap" style="background:' + bgColor + ';border-color:' + borderColor + ';color:' + accentColor + ';">' +
                            icon +
                        '</div>' +
                        '<div class="ak-success-badge" style="background:' + bgColor + ';color:' + accentColor + ';border-color:' + borderColor + ';">' +
                            escapeHtml(typeLabel) +
                        '</div>' +
                        '<h2 class="ak-success-title">' + escapeHtml(message) + '</h2>' +
                        '<p class="ak-success-subtitle">You can safely close this page.</p>' +
                        '<button type="button" class="ak-success-print-btn" onclick="window.print()">' +
                            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>' +
                            'Print this page' +
                        '</button>' +
                    '</div>' +
                '</div>';
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
