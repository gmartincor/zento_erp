const CHART_CONFIG = {
    colors: {
        primary: '#3b82f6',
        success: '#22c55e',
        danger: '#ef4444',
        warning: '#f59e0b',
        info: '#06b6d4',
        palette: ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899']
    },
    
    defaults: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top'
            }
        }
    },
    
    formatters: {
        currency: value => '€' + value.toLocaleString(),
        percentage: value => value + '%'
    }
};

class ChartFactory {
    static createLineChart(canvas, data, options = {}) {
        return new Chart(canvas, {
            type: 'line',
            data,
            options: { ...CHART_CONFIG.defaults, ...options }
        });
    }
    
    static createBarChart(canvas, data, options = {}) {
        return new Chart(canvas, {
            type: 'bar',
            data,
            options: { ...CHART_CONFIG.defaults, ...options }
        });
    }
    
    static createDoughnutChart(canvas, data, options = {}) {
        return new Chart(canvas, {
            type: 'doughnut',
            data,
            options: { ...CHART_CONFIG.defaults, ...options }
        });
    }
}

window.CHART_CONFIG = CHART_CONFIG;
window.ChartFactory = ChartFactory;
