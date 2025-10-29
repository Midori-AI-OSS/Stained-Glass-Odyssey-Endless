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

    if (Array.isArray(config.plugins)) {
      for (const plugin of config.plugins) {
        if (plugin && plugin.load && typeof plugin.load.handler === 'function' && (plugin.name === 'vite-plugin-svelte:load-custom' || plugin.name === 'vite-plugin-svelte:load-compiled-css')) {
          const original = plugin.load.handler;
          plugin.load.handler = function guardedLoad(id, ...args) {
            if (!this || !this.environment || !this.environment.config) {
              return null;
            }
            try {
              return original.call(this, id, ...args);
            } catch (error) {
              console.error('vite-plugin-svelte load error for', plugin.name, 'with id', id, error);
              throw error;
            }
          };
        }
      }
    }
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
    conditions: ['browser', 'module', 'import', 'default'],
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
