import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
        // any request starting with /api will be forwarded to your Flask back end
        '/api': {
            target: 'http://localhost:5000',
            changeOrigin: true,
            secure: false,
        },
        },
    },
});
