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
    // Vite only serves plain HTTPS (HTTP/1.1) when `proxy` is set — otherwise
    // it upgrades to Node's http2.createSecureServer, which Safari can't
    // reliably hold a connection to alongside the Vite HMR websocket over a
    // self-signed cert (surfaces as "server unexpectedly dropped the
    // connection"). This app has nothing to proxy, so the empty object here
    // exists purely to select the HTTP/1.1 code path.
    proxy: {},
  },
});
