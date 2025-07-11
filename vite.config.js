import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: true, // слушать все адреса, включая внешние
    allowedHosts: ['.ngrok-free.app'], // разрешить все поддомены ngrok
    hmr: {
      clientPort: 443, // для https-туннеля ngrok
    },
  },
});
