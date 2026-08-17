/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_LIVE_CALL_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
