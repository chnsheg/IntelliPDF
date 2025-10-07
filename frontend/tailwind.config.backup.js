/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#f0f9ff',
                    100: '#e0f2fe',
                    200: '#bae6fd',
                    300: '#7dd3fc',
                    400: '#38bdf8',
                    500: '#0ea5e9',
                    600: '#0284c7',
                    700: '#0369a1',
                    800: '#075985',
                    900: '#0c4a6e',
                },
            },
            screens: {
                'xs': '475px',
                'mobile': { 'max': '767px' },
                'tablet': { 'min': '768px', 'max': '1023px' },
                'desktop': { 'min': '1024px' },
            },
            spacing: {
                'safe-top': 'env(safe-area-inset-top)',
                'safe-bottom': 'env(safe-area-inset-bottom)',
                'safe-left': 'env(safe-area-inset-left)',
                'safe-right': 'env(safe-area-inset-right)',
            },
            animation: {
                'bounce': 'bounce 1s infinite',
            },
            keyframes: {
                bounce: {
                    '0%, 100%': {
                        transform: 'translateY(-25%)',
                        animationTimingFunction: 'cubic-bezier(0.8, 0, 1, 1)',
                    },
                    '50%': {
                        transform: 'translateY(0)',
                        animationTimingFunction: 'cubic-bezier(0, 0, 0.2, 1)',
                    },
                },
            },
            transitionDelay: {
                '100': '100ms',
                '200': '200ms',
            },
        },
    },
    plugins: [
        function ({ addUtilities }) {
            addUtilities({
                '.scrollbar-thin': {
                    'scrollbar-width': 'thin',
                    'scrollbar-color': '#cbd5e0 #f7fafc',
                },
                '.scrollbar-thin::-webkit-scrollbar': {
                    width: '8px',
                    height: '8px',
                },
                '.scrollbar-thin::-webkit-scrollbar-track': {
                    background: '#f7fafc',
                },
                '.scrollbar-thin::-webkit-scrollbar-thumb': {
                    background: '#cbd5e0',
                    borderRadius: '4px',
                },
                '.scrollbar-thin::-webkit-scrollbar-thumb:hover': {
                    background: '#a0aec0',
                },
                '.delay-100': {
                    'animation-delay': '100ms',
                },
                '.delay-200': {
                    'animation-delay': '200ms',
                },
            });
        },
    ],
}
