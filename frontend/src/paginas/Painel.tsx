import { useQuery } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import { api } from '@/lib/api';
import { useEu } from '@/lib/eu';
import type { Acao } from '@/lib/tipos';
import { fmtData } from '@/lib/formato';
import { Cabecalho, ErroCarregar, SeloColuna } from '@/components/Comuns';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

type Painel = {
  solicitacoes_abertas: number; reformas_ativas: number; acoes_bloqueadas: number; acoes_atrasadas: number;
  minhas_acoes: (Acao & { reforma: { id: number; codigo: string; titulo: string } })[];
};

export function PainelPagina() {
  const { data: eu } = useEu();
  const q = useQuery({ queryKey: ['painel'], queryFn: () => api<Painel>('/painel/') });
  const cartoes = q.data && [
    { rotulo: 'Solicitações em andamento', valor: q.data.solicitacoes_abertas, href: '/solicitacoes/' },
    { rotulo: 'Reformas ativas', valor: q.data.reformas_ativas, para: '/reformas' },
    { rotulo: 'Ações bloqueadas', valor: q.data.acoes_bloqueadas, destaque: q.data.acoes_bloqueadas > 0, para: '/reformas' },
    { rotulo: 'Ações atrasadas', valor: q.data.acoes_atrasadas, destaque: q.data.acoes_atrasadas > 0, para: '/reformas' },
  ];
  return (
    <>
      <Cabecalho titulo={`Olá, ${eu?.nome.split(' ')[0] ?? ''}`} descricao="O que precisa da sua atenção hoje."
        acao={<Button asChild><a href="/solicitacoes/nova/">Nova solicitação</a></Button>} />
      {q.error && <ErroCarregar erro={q.error} tentar={() => q.refetch()} />}
      <section aria-label="Indicadores" className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
        {!cartoes ? [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28 rounded-xl" />) : cartoes.map((c) => {
          const corpo = (
            <>
              <p className="text-sm text-muted-foreground">{c.rotulo}</p>
              <p className={`mt-2 text-3xl font-bold tabular-nums ${c.destaque ? 'text-[#a35a00]' : 'text-primary'}`}>{c.valor}</p>
            </>
          );
          const cls = `block rounded-xl border bg-card p-4 sm:p-5 shadow-card hover:border-primary/40 ${c.destaque ? 'border-warning/50' : ''}`;
          return c.href ? <a key={c.rotulo} href={c.href} className={cls}>{corpo}</a> : <Link key={c.rotulo} to={c.para!} className={cls}>{corpo}</Link>;
        })}
      </section>
      <section className="rounded-xl border bg-card p-4 sm:p-6 shadow-card">
        <h2 className="text-lg font-semibold text-primary">Minhas ações de reforma</h2>
        <p className="text-sm text-muted-foreground mb-3">Ações em que você é o colaborador responsável.</p>
        {q.isLoading ? <Skeleton className="h-24" /> : q.data!.minhas_acoes.length === 0 ? (
          <p className="py-6 text-muted-foreground">Nenhuma ação com você agora.</p>
        ) : (
          <ul className="divide-y">
            {q.data!.minhas_acoes.map((a) => (
              <li key={a.id}>
                <Link to="/reformas/$id" params={{ id: String(a.reforma.id) }} search={{ acao: a.id }} className="flex flex-col gap-1 py-3 sm:flex-row sm:items-center sm:justify-between hover:bg-muted/50 rounded-md px-2 min-h-11">
                  <span><b>{a.titulo}</b><span className="block text-sm text-muted-foreground">{a.reforma.codigo} · {a.reforma.titulo}{a.prazo ? ` · prazo ${fmtData(a.prazo)}` : ''}</span></span>
                  <SeloColuna coluna={a.coluna} />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
