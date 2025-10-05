import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'node:path';

let resolvedEnvironments;

const vitestEnvironmentShim = {
  name: 'vitest-environment-shim',
  enforce: 'pre',
  configResolved(config) {
    const assetsInclude = config.assetsInclude || (() => false);

    const environments = {
      ...(config.environments ?? {}),
      client: {
        config: {
          consumer: 'client',
          assetsInclude
        }
      }
    };

    config.environments = environments;
    resolvedEnvironments = environments;
  },
  configureServer(server) {
    if (!server || server.environments) {
      return;
    }

    if (resolvedEnvironments) {
      server.environments = resolvedEnvironments;
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
