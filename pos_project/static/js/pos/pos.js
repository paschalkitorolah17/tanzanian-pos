/**
 * POS Screen - Tanzanian POS System (Polished)
 * Features:
 * - Smart product search with debounce + skeleton loader
 * - Cart persistence (localStorage)
 * - Mixed payments (Cash, M-Pesa, Airtel Money, etc.)
 * - Real payment methods loaded from API
 * - Quick customer add
 * - Careful error handling + toasts
 * - Neon-green primary actions
 * - Opens receipt after successful sale
 * - Keyboard shortcut F2 for search
 */

(function () {
    'use strict';

    // --------------------------------------------------
    // State
    // --------------------------------------------------
    const state = {
        cart: [],
        paymentMethods: [],
        isProcessing: false,
        searchTimeout: null,
        branchId: window.POS_CONFIG?.branchId || null,
        customerId: null,
    };

    // --------------------------------------------------
    // DOM helpers
    // --------------------------------------------------
    const $  = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const searchInput     = $('#product-search');
    const suggestionsEl   = $('#suggestions');
    const searchSkeleton  = $('#search-skeleton');
    const cartBody        = $('#cart-body');
    const btnComplete     = $('#btn-complete-sale');
    const btnClear        = $('#btn-clear-cart');

    // --------------------------------------------------
    // Utility functions
    // --------------------------------------------------
    function formatMoney(value) {
        const num = Number(value) || 0;
        return 'TZS ' + num.toLocaleString('en-TZ', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    function showToast(message, type = 'success') {
        const id = 'toast-' + Date.now();
        const bg = type === 'success' ? 'bg-success' :
                   type === 'error'   ? 'bg-danger'  : 'bg-warning';

        const html = `
            <div id="${id}" class="toast align-items-center text-white ${bg} border-0 show mb-2" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>`;
        $('#toast-container').insertAdjacentHTML('beforeend', html);

        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) el.remove();
        }, 4000);
    }

    function debounce(fn, delay = 300) {
        return function (...args) {
            clearTimeout(state.searchTimeout);
            state.searchTimeout = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    // --------------------------------------------------
    // Network status + Clock
    // --------------------------------------------------
    function updateNetworkStatus() {
        const el = $('#network-status');
        if (!el) return;
        if (navigator.onLine) {
            el.className = 'network-status online';
            el.innerHTML = '<i class="bi bi-wifi"></i> Online';
        } else {
            el.className = 'network-status offline';
            el.innerHTML = '<i class="bi bi-wifi-off"></i> Offline';
        }
    }
    window.addEventListener('online',  updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);
    updateNetworkStatus();

    function updateClock() {
        const el = $('#current-time');
        if (el) el.textContent = new Date().toLocaleString('en-TZ');
    }
    setInterval(updateClock, 1000);
    updateClock();

    // --------------------------------------------------
    // Cart persistence (localStorage)
    // --------------------------------------------------
    const CART_KEY = 'pos_cart_v1';

    function saveCart() {
        try {
            localStorage.setItem(CART_KEY, JSON.stringify(state.cart));
        } catch (e) { /* ignore quota errors */ }
    }

    function loadCart() {
        try {
            const raw = localStorage.getItem(CART_KEY);
            if (raw) {
                state.cart = JSON.parse(raw);
                renderCart();
            }
        } catch (e) {
            state.cart = [];
        }
    }

    // --------------------------------------------------
    // Product Search (smart autofill + skeleton)
    // --------------------------------------------------
    const doSearch = debounce(async function (query) {
        if (!query || query.length < 1) {
            suggestionsEl.classList.remove('active');
            searchSkeleton.classList.add('d-none');
            return;
        }

        searchSkeleton.classList.remove('d-none');
        suggestionsEl.classList.remove('active');

        try {
            const res = await fetch(`/api/v1/products/search/?q=${encodeURIComponent(query)}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await res.json();

            searchSkeleton.classList.add('d-none');

            if (!data.success || !data.results.length) {
                suggestionsEl.innerHTML = '<div class="suggestion-item text-muted">No products found</div>';
                suggestionsEl.classList.add('active');
                return;
            }

            suggestionsEl.innerHTML = data.results.map(p => `
                <div class="suggestion-item"
                     data-id="${p.id}"
                     data-name="${p.name}"
                     data-sku="${p.sku}"
                     data-price="${p.selling_price}"
                     data-tax-rate="${p.tax_rate}"
                     data-tax-status="${p.tax_status}">
                    <strong>${p.name}</strong><br>
                    <small class="text-muted">${p.sku} · ${formatMoney(p.selling_price)}</small>
                </div>
            `).join('');
            suggestionsEl.classList.add('active');
        } catch (err) {
            searchSkeleton.classList.add('d-none');
            showToast('Search failed. Check connection.', 'error');
        }
    }, 300);

    searchInput.addEventListener('input', (e) => doSearch(e.target.value.trim()));

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            suggestionsEl.classList.remove('active');
        }
        if (e.key === 'Enter') {
            const first = suggestionsEl.querySelector('.suggestion-item');
            if (first) first.click();
        }
    });

    // Click suggestion → add to cart
    suggestionsEl.addEventListener('click', (e) => {
        const item = e.target.closest('.suggestion-item');
        if (!item || !item.dataset.id) return;

        addToCart({
            product_id: parseInt(item.dataset.id),
            name: item.dataset.name,
            sku: item.dataset.sku,
            unit_price: parseFloat(item.dataset.price),
            tax_rate: parseFloat(item.dataset.taxRate || 18),
            tax_status: item.dataset.taxStatus || 'taxable',
            quantity: 1,
            discount: 0
        });

        searchInput.value = '';
        suggestionsEl.classList.remove('active');
        searchInput.focus();
    });

    // --------------------------------------------------
    // Cart logic
    // --------------------------------------------------
    function addToCart(product) {
        const existing = state.cart.find(i => i.product_id === product.product_id);
        if (existing) {
            existing.quantity += 1;
        } else {
            state.cart.push({ ...product });
        }
        saveCart();
        renderCart();
        showToast(`${product.name} added`, 'success');
    }

    function updateQuantity(productId, qty) {
        const item = state.cart.find(i => i.product_id === productId);
        if (!item) return;
        item.quantity = Math.max(0.001, parseFloat(qty) || 1);
        saveCart();
        renderCart();
    }

    function removeFromCart(productId) {
        state.cart = state.cart.filter(i => i.product_id !== productId);
        saveCart();
        renderCart();
    }

    function clearCart() {
        if (!state.cart.length) return;
        if (!confirm('Clear the entire cart?')) return;
        state.cart = [];
        state.customerId = null;
        const custEl = $('#selected-customer');
        const custIdEl = $('#customer-id');
        if (custEl) custEl.textContent = 'Walk-in customer';
        if (custIdEl) custIdEl.value = '';
        saveCart();
        renderCart();
        $$('.payment-method').forEach(el => el.classList.remove('active'));
        renderPaymentInputs();
    }

    function calculateTotals() {
        let subtotal = 0, discountTotal = 0, taxTotal = 0;

        state.cart.forEach(item => {
            const line = item.unit_price * item.quantity;
            const discount = Number(item.discount) || 0;
            const taxable = line - discount;
            let tax = 0;
            if (item.tax_status === 'taxable') {
                tax = taxable * (item.tax_rate / 100);
            }
            subtotal += line;
            discountTotal += discount;
            taxTotal += tax;
        });

        return {
            subtotal,
            discountTotal,
            taxTotal,
            grand: subtotal - discountTotal + taxTotal
        };
    }

    function renderCart() {
        if (!state.cart.length) {
            cartBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-5">
                        <i class="bi bi-cart" style="font-size:2rem"></i><br>
                        Cart is empty. Scan or search a product.
                    </td>
                </tr>`;
            btnComplete.disabled = true;
            updateTotalsDisplay({ subtotal: 0, discountTotal: 0, taxTotal: 0, grand: 0 });
            return;
        }

        cartBody.innerHTML = state.cart.map(item => {
            const line = item.unit_price * item.quantity - (item.discount || 0);
            return `
                <tr data-id="${item.product_id}">
                    <td>
                        <strong>${item.name}</strong><br>
                        <small class="text-muted">${item.sku}</small>
                    </td>
                    <td>
                        <input type="number" class="form-control form-control-sm qty-input"
                               value="${item.quantity}" min="0.001" step="1" style="width:80px">
                    </td>
                    <td>${formatMoney(item.unit_price)}</td>
                    <td>
                        <input type="number" class="form-control form-control-sm discount-input"
                               value="${item.discount || 0}" min="0" step="100" style="width:80px">
                    </td>
                    <td>${formatMoney(line)}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger btn-remove">&times;</button>
                    </td>
                </tr>`;
        }).join('');

        // Bind events
        $$('.qty-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const id = parseInt(e.target.closest('tr').dataset.id);
                updateQuantity(id, e.target.value);
            });
        });

        $$('.discount-input').forEach(input => {
            input.addEventListener('change', (e) => {
                const id = parseInt(e.target.closest('tr').dataset.id);
                const item = state.cart.find(i => i.product_id === id);
                if (item) {
                    item.discount = parseFloat(e.target.value) || 0;
                    saveCart();
                    renderCart();
                }
            });
        });

        $$('.btn-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.target.closest('tr').dataset.id);
                removeFromCart(id);
            });
        });

        const totals = calculateTotals();
        updateTotalsDisplay(totals);
        btnComplete.disabled = totals.grand <= 0 || state.isProcessing;
    }

    function updateTotalsDisplay(t) {
        $('#subtotal').textContent       = formatMoney(t.subtotal);
        $('#discount-total').textContent = formatMoney(t.discountTotal);
        $('#tax-total').textContent      = formatMoney(t.taxTotal);
        $('#grand-total').textContent    = formatMoney(t.grand);
        updatePaidAndChange(t.grand);
    }

    // --------------------------------------------------
    // Payments – load from API
    // --------------------------------------------------
    async function loadPaymentMethods() {
        try {
            const res = await fetch('/api/v1/payment-methods/');
            const data = await res.json();
            if (data.success && data.results.length) {
                state.paymentMethods = data.results;
            } else {
                throw new Error('No methods');
            }
        } catch (e) {
            // Fallback if API fails
            state.paymentMethods = [
                { id: 1, name: 'Cash',         code: 'cash',   is_cash: true  },
                { id: 2, name: 'M-Pesa',       code: 'mpesa',  is_cash: false },
                { id: 3, name: 'Airtel Money', code: 'airtel', is_cash: false },
                { id: 4, name: 'Mixx by Yas',  code: 'mixx',   is_cash: false },
            ];
        }

        const container = $('#payment-methods');
        if (!container) return;

        container.innerHTML = state.paymentMethods.map(m => `
            <div class="col-6">
                <div class="payment-method text-center" data-id="${m.id}" data-cash="${m.is_cash}">
                    ${m.name}
                </div>
            </div>
        `).join('');

        $$('.payment-method').forEach(el => {
            el.addEventListener('click', () => {
                el.classList.toggle('active');
                renderPaymentInputs();
            });
        });
    }

    function renderPaymentInputs() {
        const active = $$('.payment-method.active');
        const container = $('#payment-inputs');
        if (!container) return;
        container.innerHTML = '';

        active.forEach(el => {
            const id = el.dataset.id;
            const method = state.paymentMethods.find(m => m.id == id);
            const needsRef = !method.is_cash;

            container.insertAdjacentHTML('beforeend', `
                <div class="mb-2">
                    <label class="form-label small">${method.name} Amount</label>
                    <input type="number" class="form-control payment-amount"
                           data-id="${id}" min="0" step="100" placeholder="0">
                    ${needsRef ? `
                        <input type="text" class="form-control form-control-sm mt-1 payment-ref"
                               data-id="${id}" placeholder="Reference / code">
                    ` : ''}
                </div>
            `);
        });

        $$('.payment-amount').forEach(input => {
            input.addEventListener('input', () => {
                updatePaidAndChange(calculateTotals().grand);
            });
        });
    }

    function updatePaidAndChange(grand) {
        let paid = 0;
        $$('.payment-amount').forEach(input => {
            paid += parseFloat(input.value) || 0;
        });
        const paidEl = $('#paid-total');
        if (paidEl) paidEl.textContent = formatMoney(paid);

        const change = paid - grand;
        const el = $('#change-amount');
        if (el) {
            el.textContent = formatMoney(change);
            el.style.color = change < 0 ? '#ef4444' : '#00C853';
        }
    }

    // --------------------------------------------------
    // Complete Sale (NO optimistic UI for money)
    // --------------------------------------------------
    async function completeSale() {
        if (state.isProcessing || !state.cart.length) return;

        const totals = calculateTotals();
        if (totals.grand <= 0) {
            showToast('Cart total must be greater than zero', 'error');
            return;
        }

        // Collect payments
        const payments = [];
        $$('.payment-amount').forEach(input => {
            const amount = parseFloat(input.value) || 0;
            if (amount > 0) {
                const id = input.dataset.id;
                const refInput = document.querySelector(`.payment-ref[data-id="${id}"]`);
                payments.push({
                    payment_method_id: parseInt(id),
                    amount: amount.toFixed(2),
                    reference: refInput ? refInput.value.trim() : ''
                });
            }
        });

        if (!payments.length) {
            showToast('Please enter at least one payment', 'error');
            return;
        }

        const paid = payments.reduce((s, p) => s + parseFloat(p.amount), 0);
        if (Math.abs(paid - totals.grand) > 0.5) {
            showToast(
                `Payment total (${formatMoney(paid)}) does not match sale total (${formatMoney(totals.grand)})`,
                'error'
            );
            return;
        }

        state.isProcessing = true;
        btnComplete.disabled = true;
        btnComplete.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Processing...';

        const customerId = $('#customer-id') ? $('#customer-id').value : null;

        const payload = {
            branch_id: state.branchId,
            items: state.cart.map(i => ({
                product_id: i.product_id,
                quantity: i.quantity.toString(),
                discount: (i.discount || 0).toString()
            })),
            payments: payments,
            customer_id: customerId || null,
            idempotency_key: 'pos-' + Date.now() + '-' + Math.random().toString(36).slice(2, 9)
        };

        try {
            const res = await fetch(window.POS_CONFIG.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.POS_CONFIG.csrfToken
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (data.success) {
                showToast(`Sale ${data.data.transaction_number} completed!`, 'success');

                // Clear cart + customer
                state.cart = [];
                state.customerId = null;
                if ($('#selected-customer')) $('#selected-customer').textContent = 'Walk-in customer';
                if ($('#customer-id')) $('#customer-id').value = '';
                saveCart();
                renderCart();
                $$('.payment-method').forEach(el => el.classList.remove('active'));
                renderPaymentInputs();

                                // Download PDF receipt
                const pdfUrl = `/pos/receipt/${data.data.id}/pdf/`;
                const link = document.createElement('a');
                link.href = pdfUrl;
                link.download = `receipt_${data.data.transaction_number}.pdf`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } else {
                showToast(data.message || 'Sale failed', 'error');
            }
        } catch (err) {
            showToast('Network error. Sale was not completed.', 'error');
        } finally {
            state.isProcessing = false;
            btnComplete.disabled = false;
            btnComplete.innerHTML = '<i class="bi bi-check2-circle"></i> Complete Sale';
        }
    }

    // --------------------------------------------------
    // Quick Customer
    // --------------------------------------------------
    const customerModalEl = document.getElementById('customerModal');
    let customerModal = null;
    if (customerModalEl && window.bootstrap) {
        customerModal = new bootstrap.Modal(customerModalEl);
    }

    document.getElementById('btn-add-customer')?.addEventListener('click', () => {
        const nameEl = document.getElementById('new-customer-name');
        const phoneEl = document.getElementById('new-customer-phone');
        if (nameEl) nameEl.value = '';
        if (phoneEl) phoneEl.value = '';
        if (customerModal) customerModal.show();
    });

    document.getElementById('btn-save-customer')?.addEventListener('click', async () => {
        const name = document.getElementById('new-customer-name')?.value.trim() || '';
        const phone = document.getElementById('new-customer-phone')?.value.trim() || '';

        if (!name) {
            showToast('Customer name is required', 'error');
            return;
        }

        try {
            const res = await fetch('/api/v1/customers/quick/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.POS_CONFIG.csrfToken
                },
                body: JSON.stringify({ name, phone })
            });
            const data = await res.json();

            if (data.success) {
                if ($('#customer-id')) $('#customer-id').value = data.data.id;
                if ($('#selected-customer')) {
                    $('#selected-customer').textContent =
                        `${data.data.name}${data.data.phone ? ' (' + data.data.phone + ')' : ''}`;
                }
                state.customerId = data.data.id;
                if (customerModal) customerModal.hide();
                showToast('Customer selected', 'success');
            } else {
                showToast(data.message || 'Failed to save customer', 'error');
            }
        } catch (err) {
            showToast('Network error', 'error');
        }
    });

    // --------------------------------------------------
    // Init
    // --------------------------------------------------
    if (btnClear) btnClear.addEventListener('click', clearCart);
    if (btnComplete) btnComplete.addEventListener('click', completeSale);

    // Keyboard shortcut F2 → focus search
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F2') {
            e.preventDefault();
            if (searchInput) searchInput.focus();
        }
    });

    loadCart();
    loadPaymentMethods();
    if (searchInput) searchInput.focus();
})();
