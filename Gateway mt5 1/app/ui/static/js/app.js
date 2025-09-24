// MT5 Flask Gateway - Custom JavaScript

// Utility Functions
const Utils = {
    // Format currency
    formatCurrency: (amount, currency = 'USD') => {
        return new Intl.NumberFormat('de-DE', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    // Format number with decimals
    formatNumber: (number, decimals = 2) => {
        return new Intl.NumberFormat('de-DE', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    },
    
    // Format date
    formatDate: (dateString) => {
        return new Date(dateString).toLocaleDateString('de-DE');
    },
    
    // Format datetime
    formatDateTime: (dateString) => {
        return new Date(dateString).toLocaleString('de-DE');
    },
    
    // Format time
    formatTime: (dateString) => {
        return new Date(dateString).toLocaleTimeString('de-DE');
    },
    
    // Copy text to clipboard
    copyToClipboard: async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Failed to copy text: ', err);
            return false;
        }
    },
    
    // Show notification
    showNotification: (message, type = 'info') => {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${getNotificationClass(type)}`;
        notification.textContent = message;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    },
    
    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function
    throttle: (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Notification helper
function getNotificationClass(type) {
    switch (type) {
        case 'success': return 'bg-green-100 border border-green-400 text-green-700';
        case 'error': return 'bg-red-100 border border-red-400 text-red-700';
        case 'warning': return 'bg-yellow-100 border border-yellow-400 text-yellow-700';
        default: return 'bg-blue-100 border border-blue-400 text-blue-700';
    }
}

// API Helper
const API = {
    baseURL: '/api/v1',
    
    // Generic API call
    call: async (endpoint, options = {}) => {
        const url = `${API.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': 'test_key' // Für UI-Zugriff
            }
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'API call failed');
            }
            
            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },
    
    // GET request
    get: (endpoint) => API.call(endpoint, { method: 'GET' }),
    
    // POST request
    post: (endpoint, data) => API.call(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    }),
    
    // PUT request
    put: (endpoint, data) => API.call(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),
    
    // DELETE request
    delete: (endpoint) => API.call(endpoint, { method: 'DELETE' })
};

// Chart Helper (für zukünftige Erweiterungen)
const ChartHelper = {
    // Erstellt einfache Trading-Charts
    createTradingChart: (containerId, data) => {
        // Placeholder für Chart-Implementierung
        console.log('Creating trading chart for:', containerId, data);
    },
    
    // Erstellt Performance-Chart
    createPerformanceChart: (containerId, data) => {
        // Placeholder für Performance-Chart
        console.log('Creating performance chart for:', containerId, data);
    }
};

// Form Helper
const FormHelper = {
    // Validiert Formular
    validateForm: (formElement) => {
        const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('border-red-500');
                isValid = false;
            } else {
                input.classList.remove('border-red-500');
            }
        });
        
        return isValid;
    },
    
    // Serialisiert Formular zu JSON
    serializeForm: (formElement) => {
        const formData = new FormData(formElement);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    },
    
    // Setzt Formular-Werte
    setFormValues: (formElement, data) => {
        Object.keys(data).forEach(key => {
            const input = formElement.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = data[key];
            }
        });
    }
};

// Local Storage Helper
const Storage = {
    // Speichert Daten
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
            return false;
        }
    },
    
    // Lädt Daten
    get: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Failed to load from localStorage:', error);
            return defaultValue;
        }
    },
    
    // Entfernt Daten
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Failed to remove from localStorage:', error);
            return false;
        }
    },
    
    // Leert alle Daten
    clear: () => {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Failed to clear localStorage:', error);
            return false;
        }
    }
};

// Theme Helper
const Theme = {
    // Lädt Theme aus Storage
    load: () => {
        return Storage.get('theme', 'light');
    },
    
    // Speichert Theme
    save: (theme) => {
        Storage.set('theme', theme);
    },
    
    // Setzt Theme
    set: (theme) => {
        document.documentElement.classList.remove('light', 'dark');
        document.documentElement.classList.add(theme);
        Theme.save(theme);
    },
    
    // Toggle Theme
    toggle: () => {
        const currentTheme = Theme.load();
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        Theme.set(newTheme);
        return newTheme;
    }
};

// Trading Helper
const TradingHelper = {
    // Berechnet Lot-Größe
    calculateLotSize: (balance, riskPercent, slPips, symbolInfo) => {
        const riskAmount = balance * (riskPercent / 100);
        const pipValue = symbolInfo.tick_value * symbolInfo.contract_size;
        const lossPerLot = slPips * symbolInfo.point * pipValue;
        
        if (lossPerLot <= 0) return 0;
        
        return Math.max(0.01, Math.min(100, riskAmount / lossPerLot));
    },
    
    // Berechnet SL/TP Preise
    calculateSLTP: (entryPrice, side, slPips, tpPips, symbolInfo) => {
        const pipValue = symbolInfo.point;
        
        let slPrice, tpPrice;
        
        if (side === 'buy') {
            slPrice = slPips ? entryPrice - (slPips * pipValue) : null;
            tpPrice = tpPips ? entryPrice + (tpPips * pipValue) : null;
        } else {
            slPrice = slPips ? entryPrice + (slPips * pipValue) : null;
            tpPrice = tpPips ? entryPrice - (tpPips * pipValue) : null;
        }
        
        return { slPrice, tpPrice };
    },
    
    // Formatiert Trading-Signal
    formatSignal: (signal) => {
        return {
            strategy: signal.strategy,
            symbol: signal.symbol,
            side: signal.side,
            type: signal.type,
            risk: signal.risk,
            sl: signal.sl,
            tp: signal.tp,
            comment: signal.comment || '',
            idempotency_key: signal.idempotency_key || generateIdempotencyKey()
        };
    }
};

// Generiert Idempotency-Key
function generateIdempotencyKey() {
    return 'idem_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Theme laden
    const savedTheme = Theme.load();
    Theme.set(savedTheme);
    
    // Copy-Buttons
    document.querySelectorAll('[data-copy]').forEach(button => {
        button.addEventListener('click', async () => {
            const text = button.getAttribute('data-copy');
            const success = await Utils.copyToClipboard(text);
            
            if (success) {
                Utils.showNotification('In die Zwischenablage kopiert', 'success');
            } else {
                Utils.showNotification('Fehler beim Kopieren', 'error');
            }
        });
    });
    
    // Form Validation
    document.querySelectorAll('form[data-validate]').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!FormHelper.validateForm(form)) {
                e.preventDefault();
                Utils.showNotification('Bitte füllen Sie alle Pflichtfelder aus', 'warning');
            }
        });
    });
    
    // Auto-save Forms
    document.querySelectorAll('form[data-autosave]').forEach(form => {
        const formId = form.getAttribute('data-autosave');
        
        // Form-Werte laden
        const savedData = Storage.get(`form_${formId}`);
        if (savedData) {
            FormHelper.setFormValues(form, savedData);
        }
        
        // Form-Änderungen speichern
        form.addEventListener('input', Utils.debounce(() => {
            const formData = FormHelper.serializeForm(form);
            Storage.set(`form_${formId}`, formData);
        }, 1000));
    });
});

// Export für globale Verwendung
window.MT5Gateway = {
    Utils,
    API,
    ChartHelper,
    FormHelper,
    Storage,
    Theme,
    TradingHelper
};
