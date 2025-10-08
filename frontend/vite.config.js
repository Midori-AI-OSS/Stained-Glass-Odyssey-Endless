import { sveltekit } from '@sveltejs/kit/vite';
import { createLogger, defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';

async function discoverBackend(logger) {
  const services = [
    'http://backend:59002',
    'http://backend-llm-cuda:59002',
    'http://backend-llm-amd:59002',
    'http://backend-llm-cpu:59002',
    'http://localhost:59002'
  ];

  // Check if backend is already set via environment
  if (process.env.VITE_API_BASE) {
    return process.env.VITE_API_BASE;
  }

  async function probe(url) {
    try {
      const res = await fetch(`${url}/`);
      return res.ok;
    } catch {
      return false;
    }
  }

  // Keep probing until one is found
  // Small delay helper
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  let attempt = 0;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    for (const url of services) {
      // eslint-disable-next-line no-await-in-loop
      if (await probe(url)) {
        logger?.info(`[backend] discovered ${url}, proxying via /api`);
        return url;
      }
    }
    attempt += 1;
    const waitMs = Math.min(2000, 500 + attempt * 250); // 0.5s → 2s backoff
    logger?.info(`[backend] not ready yet (attempt ${attempt}), retrying in ${waitMs}ms...`);
    // eslint-disable-next-line no-await-in-loop
    await sleep(waitMs);
  }
}

function backendDiscoveryPlugin() {
  return {
    name: 'backend-discovery',
    configureServer(server) {
      // Return /api as the API base for the frontend
      server.middlewares.use('/api-base', (_req, res) => {
        res.end('/api');
      });
    }
  };
}

export default defineConfig(async () => {
  const logger = createLogger(process.env.LOG_LEVEL || 'info');
  const isVitest = process.env.VITEST === 'true';
  const backendUrl = isVitest
    ? (process.env.VITE_API_BASE || 'http://localhost')
    : await discoverBackend(logger);
  
  return {
    plugins: [
      sveltekit(),
      viteStaticCopy({
        targets: [
          {
            src: 'node_modules/@zaniar/effekseer-webgl-wasm/effekseer.wasm',
            dest: ''
          }
        ]
      }),
      ...(isVitest ? [] : [backendDiscoveryPlugin()])
    ],
    server: {
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    assetsInclude: ['**/*.efkefc'],
    test: {
      environment: 'jsdom',
      setupFiles: ['./vitest.setup.js'],
      include: ['tests/**/*.vitest.{js,ts}'],
      css: true
    }
  };
});
