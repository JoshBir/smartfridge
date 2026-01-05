/* SmartFridge - JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const message = this.getAttribute('data-confirm') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // Auto-focus first input in forms
    const forms = document.querySelectorAll('form:not(.no-autofocus)');
    forms.forEach(function(form) {
        const firstInput = form.querySelector('input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), textarea, select');
        if (firstInput && !firstInput.value) {
            firstInput.focus();
        }
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.05) + 's';
        card.classList.add('fade-in');
    });

    // Expiry date picker enhancement
    const expiryInputs = document.querySelectorAll('input[type="date"][name*="expiry"]');
    expiryInputs.forEach(function(input) {
        // Set min date to today
        const today = new Date().toISOString().split('T')[0];
        if (!input.getAttribute('min')) {
            input.setAttribute('min', today);
        }
    });

    // Quantity input with +/- buttons
    const quantityInputs = document.querySelectorAll('input[type="number"][name="quantity"]');
    quantityInputs.forEach(function(input) {
        const wrapper = document.createElement('div');
        wrapper.className = 'input-group';
        
        const minusBtn = document.createElement('button');
        minusBtn.type = 'button';
        minusBtn.className = 'btn btn-outline-secondary';
        minusBtn.innerHTML = '<i class="bi bi-dash"></i>';
        minusBtn.addEventListener('click', function() {
            const currentVal = parseInt(input.value) || 0;
            if (currentVal > (parseInt(input.min) || 1)) {
                input.value = currentVal - 1;
                input.dispatchEvent(new Event('change'));
            }
        });
        
        const plusBtn = document.createElement('button');
        plusBtn.type = 'button';
        plusBtn.className = 'btn btn-outline-secondary';
        plusBtn.innerHTML = '<i class="bi bi-plus"></i>';
        plusBtn.addEventListener('click', function() {
            const currentVal = parseInt(input.value) || 0;
            const max = parseInt(input.max) || 9999;
            if (currentVal < max) {
                input.value = currentVal + 1;
                input.dispatchEvent(new Event('change'));
            }
        });
        
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(minusBtn);
        wrapper.appendChild(input);
        wrapper.appendChild(plusBtn);
    });

    // Search form enhancements
    const searchForms = document.querySelectorAll('form[action*="search"], form input[name="search"]');
    searchForms.forEach(function(form) {
        const input = form.querySelector('input[name="search"], input[name="q"]');
        if (input) {
            // Clear button
            const clearBtn = document.createElement('button');
            clearBtn.type = 'button';
            clearBtn.className = 'btn btn-outline-secondary';
            clearBtn.innerHTML = '<i class="bi bi-x"></i>';
            clearBtn.style.display = input.value ? 'block' : 'none';
            clearBtn.addEventListener('click', function() {
                input.value = '';
                input.focus();
                clearBtn.style.display = 'none';
            });
            
            input.addEventListener('input', function() {
                clearBtn.style.display = this.value ? 'block' : 'none';
            });
            
            if (input.parentElement.classList.contains('input-group')) {
                input.parentElement.appendChild(clearBtn);
            }
        }
    });

    // Tooltip initialisation
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Tag input enhancement
    const tagInputs = document.querySelectorAll('input[name="tags"]');
    tagInputs.forEach(function(input) {
        input.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                // Prevent form submission, add comma instead
                const value = this.value.trim();
                if (value && !value.endsWith(',')) {
                    event.preventDefault();
                    this.value = value + ', ';
                }
            }
        });
    });

    // Print recipe functionality
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Clipboard copy functionality
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', async function() {
            const target = this.getAttribute('data-copy');
            const element = document.querySelector(target);
            if (element) {
                try {
                    await navigator.clipboard.writeText(element.textContent || element.value);
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i class="bi bi-check"></i> Copied!';
                    setTimeout(() => {
                        this.innerHTML = originalText;
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy:', err);
                }
            }
        });
    });

    // Form validation enhancement
    const formsNeedingValidation = document.querySelectorAll('form.needs-validation');
    formsNeedingValidation.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Auto-save draft functionality (for recipe/site forms)
    const draftForms = document.querySelectorAll('form[data-autosave]');
    draftForms.forEach(function(form) {
        const key = 'smartfridge_draft_' + form.getAttribute('data-autosave');
        
        // Load saved draft
        const savedDraft = localStorage.getItem(key);
        if (savedDraft) {
            try {
                const draft = JSON.parse(savedDraft);
                Object.keys(draft).forEach(function(name) {
                    const input = form.querySelector(`[name="${name}"]`);
                    if (input && !input.value) {
                        input.value = draft[name];
                    }
                });
            } catch (e) {
                console.error('Error loading draft:', e);
            }
        }
        
        // Save draft on input
        form.addEventListener('input', debounce(function() {
            const formData = new FormData(form);
            const draft = {};
            formData.forEach(function(value, key) {
                if (key !== 'csrf_token') {
                    draft[key] = value;
                }
            });
            localStorage.setItem(key, JSON.stringify(draft));
        }, 1000));
        
        // Clear draft on successful submit
        form.addEventListener('submit', function() {
            localStorage.removeItem(key);
        });
    });

    // Utility: Debounce function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Dark mode toggle (if enabled)
    const darkModeToggle = document.querySelector('#darkModeToggle');
    if (darkModeToggle) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
            darkModeToggle.checked = true;
        }
        
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.documentElement.setAttribute('data-bs-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.setAttribute('data-bs-theme', 'light');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    console.log('SmartFridge JS initialised');
});
