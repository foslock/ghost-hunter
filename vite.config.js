import { defineConfig } from 'vite';
import path from 'node:path';

export default defineConfig({
  root: 'client',
  publicDir: 'public',
  server: { fs: { allow: [path.resolve('.')] } },
  build: { outDir: '../dist', emptyOutDir: true, chunkSizeWarningLimit: 1500, target: 'es2022' },
});
