import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  server: {
    port: 3000,
    strictPort: true,
  },
  root: './',
  build: {
    outDir: 'dist',
  }
});
