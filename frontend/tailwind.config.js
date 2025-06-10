/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,jsx,ts,tsx}"
    ],
    theme: {
        extend: {
            colors: {
                laliga: {
                    primary: "#3A0CA3",
                    secondary: "#F72585",
                    yellow: "#FFBA08"
                }
            }
        },
    },
    plugins: [],
};
