import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRootRoute, createRoute, createRouter, RouterProvider } from '@tanstack/react-router';
import { setNonce } from 'get-nonce';
import './styles.css';
import { AppShell } from '@/components/AppShell';
import { AvisosProvider } from '@/components/Avisos';
import { PainelPagina } from '@/paginas/Painel';
import { ReformasPagina } from '@/paginas/Reformas';
import { NovaReformaPagina } from '@/paginas/NovaReforma';
import { ReformaDetalhePagina } from '@/paginas/ReformaDetalhe';
import { ErroApi } from '@/lib/api';

// Nonce da CSP entregue pelo Django: libera só os <style> que o Radix cria (trava de rolagem dos diálogos).
const nonce = document.querySelector<HTMLMetaElement>('meta[name="csp-nonce"]')?.content;
if (nonce && nonce !== '__CSP_NONCE__') setNonce(nonce);

const raiz = createRootRoute({
  component: AppShell,
  notFoundComponent: () => <p className="text-muted-foreground">Página não encontrada.</p>,
});
const painel = createRoute({ getParentRoute: () => raiz, path: '/', component: PainelPagina });
const reformas = createRoute({ getParentRoute: () => raiz, path: '/reformas', component: ReformasPagina });
const nova = createRoute({ getParentRoute: () => raiz, path: '/reformas/nova', component: NovaReformaPagina });
const detalhe = createRoute({
  getParentRoute: () => raiz,
  path: '/reformas/$id',
  validateSearch: (s: Record<string, unknown>): { acao?: number } => {
    const n = Number(s.acao);
    return Number.isInteger(n) && n > 0 ? { acao: n } : {};
  },
  component: function Detalhe() {
    const { id } = detalhe.useParams();
    const { acao } = detalhe.useSearch();
    return <ReformaDetalhePagina key={id} id={Number(id)} acaoAberta={acao} />;
  },
});

const router = createRouter({ routeTree: raiz.addChildren([painel, reformas, nova, detalhe]), defaultPreload: 'intent' });
declare module '@tanstack/react-router' {
  interface Register { router: typeof router }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      retry: (n, e) => !(e instanceof ErroApi && e.status < 500) && n < 2,
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AvisosProvider>
        <RouterProvider router={router} />
      </AvisosProvider>
    </QueryClientProvider>
  </StrictMode>,
);
