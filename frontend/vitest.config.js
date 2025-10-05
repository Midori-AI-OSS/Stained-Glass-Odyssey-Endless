import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'node:path';

const vitestEnvironmentShim = {
  name: 'vitest-environment-shim',
  enforce: 'pre',
  configureServer(server) {
    if (!server) {
      return;
    }
    if (!server.environments) {
      const assetsInclude = server.config?.assetsInclude || (() => false);
      server.environments = {
        client: {
          config: {
            consumer: 'client',
            assetsInclude
          }
        }
      };
    }
  }
};

export default defineConfig({
  plugins: [
    vitestEnvironmentShim,
    svelte({
      hot: false
    })
  ],
  resolve: {
    alias: {
      $lib: path.resolve('./src/lib'),
      '$app/environment': path.resolve('./src/lib/mocks/app-environment.js')
    }
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.js'],
    include: ['tests/**/*.vitest.{js,ts}'],
    css: true
  }
});
