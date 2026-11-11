import { useQuery } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import { CalendarDays, CircleAlert, HardHat, Plus } from 'lucide-react';
import { api } from '@/lib/api';
import { useEu } from '@/lib/eu';
import type { Reforma } from '@/lib/tipos';
import { fmtData } from '@/lib/formato';
import { BarraProgresso, Cabecalho, ErroCarregar } from '@/components/Comuns';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

const SITUACOES = [['', 'Todas'], ['PLANEJADA', 'Planejadas'], ['EM_ANDAMENTO', 'Em andamento'], ['PAUSADA', 'Pausadas'], ['CONCLUIDA', 'Concluídas']] as const;

export function ReformasPagina() {
  const { data: eu } = useEu();
  const [unidade, setUnidade] = useState('');
  const [situacao, setSituacao] = useState('');
  const q = useQuery({
    queryKey: ['reformas', unidade, situacao],
    queryFn: () => api<Reforma[]>(`/reformas/?${new URLSearchParams({ ...(unidade && { unidade }), ...(situacao && { situacao }) })}`),
  });
  const podeCriar = eu?.unidades.some((u) => u.pode_gerir);
  return (
    <>
      <Cabecalho titulo="Reformas dos PAs" descricao="Quem está fazendo o quê em cada obra, onde parou e quem continua."
        acao={podeCriar && <Button asChild><Link to="/reformas/nova"><Plus className="size-4" aria-hidden />Nova reforma</Link></Button>} />
      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <label className="flex flex-col gap-1 text-sm font-medium">PA
          <select value={unidade} onChange={(e) => setUnidade(e.target.value)} className="h-11 rounded-md border border-input bg-card px-3 sm:w-64">
            <option value="">Todos os PAs</option>
            {eu?.unidades.map((u) => <option key={u.id} value={u.id}>{u.code} · {u.name}</option>)}
          </select>
        </label>
        <fieldset className="flex flex-col gap-1 text-sm font-medium">
          <legend className="mb-1">Situação</legend>
          <div className="flex flex-wrap gap-2">
            {SITUACOES.map(([v, r]) => (
              <button key={v} type="button" aria-pressed={situacao === v} onClick={() => setSituacao(v)}
                className={`h-11 rounded-md border px-3 text-sm ${situacao === v ? 'border-primary bg-primary text-primary-foreground' : 'bg-card hover:border-primary/40'}`}>{r}</button>
            ))}
          </div>
        </fieldset>
      </div>
      {q.error && <ErroCarregar erro={q.error} tentar={() => q.refetch()} />}
      {q.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-48 rounded-xl" />)}</div>
      ) : q.data && q.data.length === 0 ? (
        <div className="rounded-xl border border-dashed bg-card p-10 text-center">
          <HardHat className="mx-auto size-10 text-muted-foreground" aria-hidden />
          <p className="mt-3 font-semibold">Nenhuma reforma encontrada</p>
          <p className="text-muted-foreground text-sm">{podeCriar ? 'Abra a primeira reforma e organize as ações em um quadro.' : 'Quando um gestor abrir uma reforma no seu PA, ela aparece aqui.'}</p>
        </div>
      ) : (
        <ul className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {q.data?.map((r) => (
            <li key={r.id}>
              <Link to="/reformas/$id" params={{ id: String(r.id) }} className="flex h-full flex-col gap-4 rounded-xl border bg-card p-5 shadow-card hover:border-primary/40">
                <div>
                  <p className="text-xs font-semibold text-brand-teal-ink">{r.codigo} · {r.unidade.code} {r.unidade.name}</p>
                  <h2 className="mt-1 text-lg font-semibold text-primary">{r.titulo}</h2>
                  <p className="text-sm text-muted-foreground">{r.situacao_rotulo}{r.responsavel ? ` · ${r.responsavel.nome}` : ''}</p>
                </div>
                <BarraProgresso valor={r.progresso.percentual} rotulo={`${r.progresso.concluidas} de ${r.progresso.total} ações concluídas`} />
                <div className="mt-auto flex flex-wrap gap-x-4 gap-y-1 text-sm">
                  {r.fim_previsto && <span className="inline-flex items-center gap-1 text-muted-foreground"><CalendarDays className="size-4" aria-hidden />Previsão {fmtData(r.fim_previsto)}</span>}
                  {r.progresso.bloqueadas > 0 && <span className="inline-flex items-center gap-1 font-semibold text-[#a35a00]"><CircleAlert className="size-4" aria-hidden />{r.progresso.bloqueadas} bloqueada{r.progresso.bloqueadas > 1 ? 's' : ''}</span>}
                  {r.progresso.atrasadas > 0 && <span className="font-semibold text-destructive">{r.progresso.atrasadas} atrasada{r.progresso.atrasadas > 1 ? 's' : ''}</span>}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
