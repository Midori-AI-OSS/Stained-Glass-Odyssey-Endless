import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'node:path';

let resolvedEnvironments;

const vitestEnvironmentShim = {
  name: 'vitest-environment-shim',
  enforce: 'pre',
  configResolved(config) {
    const assetsInclude = config.assetsInclude || (function() { return false });

    const environments = {
      ...(config.environments ?? {}),
      client: {
        config: {
          consumer: 'client',
          assetsInclude
        }
      },
      server: {
        config: {
          consumer: 'server',
          assetsInclude
        }
      }
    };

    config.environments = environments;
    resolvedEnvironments = environments;
  },
  configureServer(server) {
    if (!server) {
      return;
    }

    if (!resolvedEnvironments) {
      resolvedEnvironments = {
        client: {
          config: {
            consumer: 'client',
            assetsInclude: () => false
          }
        },
        server: {
          config: {
            consumer: 'server',
            assetsInclude: () => false
          }
        }
      };
    }

    if (!server.environments || typeof server.environments !== 'object') {
      server.environments = {};
    }
    server.environments.client = resolvedEnvironments.client;
    server.environments.server = resolvedEnvironments.server;
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
