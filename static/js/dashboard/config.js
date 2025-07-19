window.dashboardConfig = {
    colors: {
        primary: '#3B82F6',
        success: '#10B981', 
        danger: '#EF4444',
        warning: '#F59E0B',
        info: '#06B6D4',
        light: '#F3F4F6',
        dark: '#1F2937'
    },
    
    chartDefaults: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'bottom'
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: '#E5E7EB'
                }
            },
            x: {
                grid: {
                    color: '#E5E7EB'
                }
            }
        }
    },

    periods: {
        30: '30 días',
        90: '90 días', 
        365: '1 año',
        all: 'Todo'
    }
};
