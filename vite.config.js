import { spawnSync } from 'node:child_process';
import path from 'node:path';
import process from 'node:process';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

function restaurantWorkbookSync() {
  let timer;
  return {
    name: 'restaurant-workbook-sync',
    configureServer(server) {
      const workbook = path.resolve('data/HanoiFoodPlaces.xlsx');
      server.watcher.add(workbook);
      const sync = changedPath => {
        if (path.resolve(changedPath) !== workbook) return;
        clearTimeout(timer);
        timer = setTimeout(() => {
          const result = spawnSync('python', ['scripts/sync_restaurants.py'], { cwd: process.cwd(), encoding: 'utf8' });
          if (result.status !== 0) {
            server.config.logger.error(result.stderr || 'Could not sync restaurant workbook.');
            return;
          }
          server.config.logger.info(result.stdout.trim());
          server.ws.send({ type: 'full-reload' });
        }, 800);
      };
      server.watcher.on('change', sync);
      server.watcher.on('add', sync);
    },
  };
}

export default defineConfig({
  base: process.env.GITHUB_PAGES === 'true' ? '/HANOI-FOOD-MAP/' : '/',
  plugins: [react(), restaurantWorkbookSync()],
});
