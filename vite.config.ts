import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Locally-trusted cert (see `mkcert` in .cert/) so getUserMedia (mic access)
// works when this dev server is opened from another device on the LAN —
// browsers only allow it over HTTPS or localhost.
const keyPath = fileURLToPath(new URL('./.cert/key.pem', import.meta.url));
const certPath = fileURLToPath(new URL('./.cert/cert.pem', import.meta.url));
const https = existsSync(keyPath) && existsSync(certPath)
  ? { key: readFileSync(keyPath), cert: readFileSync(certPath) }
  : undefined;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    https,
  },
});
