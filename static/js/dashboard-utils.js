class DashboardUtils {
    static formatCurrency(value, locale = 'es-ES', currency = 'EUR') {
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency
        }).format(value);
    }

    static formatPercentage(value, decimals = 1) {
        return value.toFixed(decimals) + '%';
    }

    static calculateMargin(profit, revenue) {
        return revenue > 0 ? ((profit / revenue) * 100) : 0;
    }

    static getCanvasElement(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Canvas element with id '${id}' not found`);
        }
        return element;
    }

    static validateData(data, requiredFields = []) {
        if (!data || typeof data !== 'object') {
            return false;
        }
        
        return requiredFields.every(field => 
            data.hasOwnProperty(field) && data[field] !== null && data[field] !== undefined
        );
    }

    static sanitizeChartData(data) {
        if (!Array.isArray(data)) return [];
        
        return data.map(item => ({
            ...item,
            ingresos: Number(item.ingresos) || 0,
            gastos: Number(item.gastos) || 0,
            beneficio: Number(item.beneficio) || 0,
            total: Number(item.total) || 0
        }));
    }

    static debounce(func, wait) {
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
}

window.DashboardUtils = DashboardUtils;
