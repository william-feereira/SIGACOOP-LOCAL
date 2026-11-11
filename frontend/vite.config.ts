import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { fileURLToPath, URL } from 'node:url';

// Em produção o Django entrega index.html e os arquivos ficam em /static/app/.
// Em desenvolvimento o Vite repassa API, login e admin para o Django (porta 8000).
const django = 'http://127.0.0.1:8000';
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/app/' : '/',
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: {
    proxy: Object.fromEntries(['/api', '/contas', '/admin', '/static', '/solicitacoes', '/ativos', '/frota', '/viagens', '/contratos', '/analytics', '/privacidade', '/termos'].map((p) => [p, django])),
  },
  build: { outDir: 'dist', assetsDir: 'assets', sourcemap: false },
  test: { environment: 'node' },
}));
