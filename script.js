/**
 * SmartPantry — script.js
 * Small, focused helpers for form validation and UX improvements.
 */

"use strict";

// ---------------------------------------------------------------------------
// Delete confirmation dialog
// ---------------------------------------------------------------------------

/**
 * Ask the user to confirm before submitting a delete form.
 * Returning false prevents the form from submitting.
 *
 * @param {string} itemName - Name of the ingredient being deleted.
 * @returns {boolean}
 */
function confirmDelete(itemName) {
  return window.confirm(`Remove "${itemName}" from your pantry?`);
}

// ---------------------------------------------------------------------------
// Add-item form — client-side validation
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("addItemForm");
  if (!form) return;

  const purchaseInput = document.getElementById("purchase_date");
  const expiryInput   = document.getElementById("expiry_date");
  const expiryFeedback = document.getElementById("expiryFeedback");

  /**
   * Validate that the expiry date is not before the purchase date.
   * The server performs this check too, but doing it client-side avoids
   * an unnecessary round-trip.
   *
   * @returns {boolean}
   */
  function validateDates() {
    if (!purchaseInput.value || !expiryInput.value) return true; // let required check handle it

    const purchase = new Date(purchaseInput.value);
    const expiry   = new Date(expiryInput.value);

    if (expiry < purchase) {
      expiryInput.setCustomValidity("Expiry date cannot be earlier than purchase date.");
      if (expiryFeedback) {
        expiryFeedback.textContent = "Expiry date cannot be earlier than the purchase date.";
      }
      return false;
    }

    expiryInput.setCustomValidity("");
    return true;
  }

  // Revalidate whenever either date changes
  purchaseInput.addEventListener("change", validateDates);
  expiryInput.addEventListener("change",   validateDates);

  form.addEventListener("submit", (e) => {
    if (!validateDates() || !form.checkValidity()) {
      e.preventDefault();
      e.stopPropagation();
    }
    form.classList.add("was-validated");
  });
});

// ---------------------------------------------------------------------------
// Auto-dismiss flash alerts after 4 seconds
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  const alerts = document.querySelectorAll(".sp-alert");

  alerts.forEach((alert) => {
    setTimeout(() => {
      // Use Bootstrap's Collapse API to fade the alert out
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 4000);
  });
});