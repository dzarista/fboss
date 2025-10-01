import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'  // ← correct import :contentReference[oaicite:0]{index=0}

export default defineConfig(({ command }) => ({
  plugins: [
    react(),
    // only apply the singlefile plugin on "build", not on "serve"
    (command === 'build' && viteSingleFile())            // :contentReference[oaicite:1]{index=1}
  ].filter(Boolean)
}))