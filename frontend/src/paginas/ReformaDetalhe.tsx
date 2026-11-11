import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from '@tanstack/react-router';
import { useState, type FormEvent } from 'react';
import { ArrowLeft, CalendarDays, CircleAlert, Plus, Wallet } from 'lucide-react';
import { api, ErroApi } from '@/lib/api';
import type { ColunaId, Fornecedor, Pessoa, Prioridade, ReformaDetalhe, Registro } from '@/lib/tipos';
import { ROTULO_COLUNA, ROTULO_PRIORIDADE } from '@/lib/tipos';
import { moverLocal } from '@/lib/kanban';
import { fmtData, fmtMoeda } from '@/lib/formato';
import { useAvisos } from '@/components/Avisos';
import { BarraProgresso, Cabecalho, ErroCarregar } from '@/components/Comuns';
import { Quadro } from './Quadro';
import { AcaoPainel, ListaRegistros } from './AcaoPainel';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';

const campoSelect = 'h-11 w-full rounded-md border border-input bg-card px-3';
type Movimento = { id: number; coluna: ColunaId; indice: number };

export function ReformaDetalhePagina({ id, acaoAberta }: { id: number; acaoAberta?: number }) {
  const qc = useQueryClient();
  const avisar = useAvisos();
  const navegar = useNavigate();
  const chave = ['reforma', id];
  const q = useQuery({ queryKey: chave, queryFn: () => api<ReformaDetalhe>(`/reformas/${id}/`), refetchInterval: 20_000 });
  const [pedindoMotivo, setPedindoMotivo] = useState<Movimento | null>(null);
  const [novaAcao, setNovaAcao] = useState(false);

  const abrir = (acao: number | undefined) =>
    navegar({ to: '/reformas/$id', params: { id: String(id) }, search: acao ? { acao } : {}, replace: true });

  const mover = useMutation({
    mutationFn: ({ id: acaoId, coluna, indice, motivo }: Movimento & { motivo?: string }) => {
      const versao = q.data!.acoes.find((a) => a.id === acaoId)!.versao;
      return api(`/acoes/${acaoId}/mover/`, { corpo: { coluna, posicao: indice, versao, motivo_bloqueio: motivo ?? '' } });
    },
    onMutate: async (mv) => {
      await qc.cancelQueries({ queryKey: chave });
      const antes = qc.getQueryData<ReformaDetalhe>(chave);
      if (antes) qc.setQueryData<ReformaDetalhe>(chave, { ...antes, acoes: moverLocal(antes.acoes, mv.id, mv.coluna, mv.indice) });
      return { antes };
    },
    onError: (e, _mv, ctx) => {
      if (ctx?.antes) qc.setQueryData(chave, ctx.antes);
      const conflito = e instanceof ErroApi && e.codigo === 'conflito';
      avisar('erro', conflito ? 'Alguém alterou esta ação agora há pouco. O quadro foi atualizado; tente de novo.' : (e as Error).message);
    },
    onSuccess: (_r, mv) => avisar('ok', `Movida para "${ROTULO_COLUNA[mv.coluna]}".`),
    onSettled: () => { qc.invalidateQueries({ queryKey: chave }); qc.invalidateQueries({ queryKey: ['linha', id] }); },
  });

  function aoMover(acaoId: number, coluna: ColunaId, indice: number) {
    if (coluna === 'BLOQUEADA') setPedindoMotivo({ id: acaoId, coluna, indice });
    else mover.mutate({ id: acaoId, coluna, indice });
  }

  if (q.isPending) return <div className="space-y-4"><Skeleton className="h-10 w-1/2" /><Skeleton className="h-4 w-1/3" /><Skeleton className="h-96" /></div>;
  if (q.isError) return <ErroCarregar erro={q.error} tentar={() => q.refetch()} />;
  const r = q.data;

  return (
    <>
      <Link to="/reformas" className="mb-3 inline-flex min-h-11 items-center gap-2 text-sm text-muted-foreground hover:text-primary">
        <ArrowLeft className="size-4" aria-hidden />Todas as reformas
      </Link>
      <Cabecalho sobretitulo={`${r.codigo} · ${r.unidade.code} ${r.unidade.name}`} titulo={r.titulo}
        descricao={<span className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <span>{r.situacao_rotulo}</span>
          {r.responsavel && <span>Responsável: {r.responsavel.nome}</span>}
          {r.fim_previsto && <span className="inline-flex items-center gap-1"><CalendarDays className="size-4" aria-hidden />Entrega prevista {fmtData(r.fim_previsto)}</span>}
          {r.orcamento && <span className="inline-flex items-center gap-1"><Wallet className="size-4" aria-hidden />Orçamento {fmtMoeda(r.orcamento)}</span>}
        </span>}
        acao={r.pode_editar && <Button onClick={() => setNovaAcao(true)}><Plus className="size-4" aria-hidden />Nova ação</Button>} />

      <div className="mb-6 grid grid-cols-3 gap-4 rounded-xl border bg-card p-4 sm:grid-cols-[2fr_1fr_1fr_1fr]">
        <div className="col-span-3 sm:col-span-1"><BarraProgresso valor={r.progresso.percentual} rotulo={`${r.progresso.concluidas} de ${r.progresso.total} ações concluídas`} /></div>
        <Numero rotulo="Paradas" valor={r.progresso.bloqueadas} alerta={r.progresso.bloqueadas > 0} />
        <Numero rotulo="Atrasadas" valor={r.progresso.atrasadas} alerta={r.progresso.atrasadas > 0} />
        <Numero rotulo="Total" valor={r.progresso.total} />
      </div>

      <Tabs defaultValue="quadro">
        <TabsList className="mb-4">
          <TabsTrigger value="quadro" className="min-h-11 px-4">Quadro</TabsTrigger>
          <TabsTrigger value="linha" className="min-h-11 px-4">Linha do tempo</TabsTrigger>
        </TabsList>
        <TabsContent value="quadro">
          {!r.pode_editar && <p className="mb-3 text-sm text-muted-foreground">Você acompanha esta reforma em modo leitura.</p>}
          <Quadro acoes={r.acoes} podeEditar={r.pode_editar} aoAbrir={abrir} aoMover={aoMover} />
        </TabsContent>
        <TabsContent value="linha"><LinhaDoTempo id={id} /></TabsContent>
      </Tabs>

      <AcaoPainel acaoId={acaoAberta ?? null} reformaId={id} aoFechar={() => abrir(undefined)} />
      <DialogoMotivo mv={pedindoMotivo} aoFechar={() => setPedindoMotivo(null)} aoConfirmar={(motivo) => { mover.mutate({ ...pedindoMotivo!, motivo }); setPedindoMotivo(null); }} />
      {r.pode_editar && <DialogoNovaAcao aberto={novaAcao} aoFechar={() => setNovaAcao(false)} reforma={r} />}
    </>
  );
}

function Numero({ rotulo, valor, alerta }: { rotulo: string; valor: number; alerta?: boolean }) {
  return (
    <div className="flex flex-col items-start">
      <span className={`text-2xl font-bold tabular-nums ${alerta ? 'text-destructive' : 'text-primary'}`}>{valor}</span>
      <span className="text-sm text-muted-foreground inline-flex items-center gap-1">{alerta && <CircleAlert className="size-3.5" aria-hidden />}{rotulo}</span>
    </div>
  );
}

function LinhaDoTempo({ id }: { id: number }) {
  const q = useQuery({ queryKey: ['linha', id], queryFn: () => api<Registro[]>(`/reformas/${id}/linha-do-tempo/`) });
  if (q.isPending) return <Skeleton className="h-60" />;
  if (q.isError) return <ErroCarregar erro={q.error} tentar={() => q.refetch()} />;
  return <div className="max-w-3xl rounded-xl border bg-card p-6"><ListaRegistros registros={q.data} mostrarAcao /></div>;
}

function DialogoMotivo({ mv, aoFechar, aoConfirmar }: { mv: Movimento | null; aoFechar: () => void; aoConfirmar: (motivo: string) => void }) {
  const [motivo, setMotivo] = useState('');
  return (
    <Dialog open={mv !== null} onOpenChange={(a) => { if (!a) { aoFechar(); setMotivo(''); } }}>
      <DialogContent>
        <form onSubmit={(e) => { e.preventDefault(); aoConfirmar(motivo.trim()); setMotivo(''); }}>
          <DialogHeader>
            <DialogTitle>Por que esta ação vai parar?</DialogTitle>
            <DialogDescription>Quem abrir o cartão depois vai ver este motivo. Seja específico.</DialogDescription>
          </DialogHeader>
          <Label htmlFor="motivo-quadro" className="sr-only">Motivo</Label>
          <Textarea id="motivo-quadro" className="my-4" required autoFocus value={motivo} onChange={(e) => setMotivo(e.target.value)} placeholder="Ex.: aguardando liberação da prefeitura" />
          <DialogFooter className="gap-2">
            <Button type="button" variant="ghost" onClick={aoFechar}>Cancelar</Button>
            <Button type="submit" disabled={!motivo.trim()}>Pausar ação</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

const vazio = { titulo: '', descricao: '', quem: '', prazo: '', prioridade: 'NORMAL' as Prioridade, depende_de: '' };

function DialogoNovaAcao({ aberto, aoFechar, reforma }: { aberto: boolean; aoFechar: () => void; reforma: ReformaDetalhe }) {
  const qc = useQueryClient();
  const avisar = useAvisos();
  const [d, setD] = useState(vazio);
  const pessoas = useQuery({ queryKey: ['pessoas'], queryFn: () => api<Pessoa[]>('/pessoas/'), enabled: aberto });
  const fornecedores = useQuery({ queryKey: ['fornecedores'], queryFn: () => api<Fornecedor[]>('/fornecedores/'), enabled: aberto });
  const m = useMutation({
    mutationFn: () => {
      const [tipo, quem] = d.quem.split(':');
      return api(`/reformas/${reforma.id}/acoes/`, { corpo: {
        titulo: d.titulo, descricao: d.descricao, prioridade: d.prioridade, prazo: d.prazo || null,
        responsavel: tipo === 'u' ? Number(quem) : null, fornecedor: tipo === 'f' ? Number(quem) : null,
        depende_de: d.depende_de ? Number(d.depende_de) : null } });
    },
    onSuccess: () => { avisar('ok', 'Ação criada em "A fazer".'); setD(vazio); aoFechar(); qc.invalidateQueries({ queryKey: ['reforma', reforma.id] }); },
    onError: (e) => avisar('erro', (e as Error).message),
  });
  const set = (k: keyof typeof vazio) => (e: { target: { value: string } }) => setD((x) => ({ ...x, [k]: e.target.value }));
  const enviar = (e: FormEvent) => { e.preventDefault(); m.mutate(); };
  return (
    <Dialog open={aberto} onOpenChange={(a) => !a && aoFechar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <form onSubmit={enviar} className="space-y-4">
          <DialogHeader><DialogTitle>Nova ação</DialogTitle><DialogDescription>Ela entra na coluna "A fazer".</DialogDescription></DialogHeader>
          <div className="space-y-1"><Label htmlFor="na-titulo">O que precisa ser feito</Label>
            <Input id="na-titulo" required maxLength={160} value={d.titulo} onChange={set('titulo')} placeholder="Ex.: Trocar piso do salão" /></div>
          <div className="space-y-1"><Label htmlFor="na-desc">Detalhes (opcional)</Label>
            <Textarea id="na-desc" value={d.descricao} onChange={set('descricao')} /></div>
          <div className="space-y-1"><Label htmlFor="na-quem">Quem faz</Label>
            <select id="na-quem" className={campoSelect} value={d.quem} onChange={set('quem')}>
              <option value="">A definir</option>
              <optgroup label="Pessoas">{pessoas.data?.map((p) => <option key={p.id} value={`u:${p.id}`}>{p.nome}</option>)}</optgroup>
              <optgroup label="Empresas terceirizadas">{fornecedores.data?.map((f) => <option key={f.id} value={`f:${f.id}`}>{f.nome}</option>)}</optgroup>
            </select></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1"><Label htmlFor="na-prazo">Prazo</Label><Input id="na-prazo" type="date" value={d.prazo} onChange={set('prazo')} /></div>
            <div className="space-y-1"><Label htmlFor="na-prio">Prioridade</Label>
              <select id="na-prio" className={campoSelect} value={d.prioridade} onChange={set('prioridade')}>
                {Object.entries(ROTULO_PRIORIDADE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select></div>
          </div>
          <div className="space-y-1"><Label htmlFor="na-dep">Só pode começar depois de (opcional)</Label>
            <select id="na-dep" className={campoSelect} value={d.depende_de} onChange={set('depende_de')}>
              <option value="">Nenhuma</option>
              {reforma.acoes.map((a) => <option key={a.id} value={a.id}>{a.titulo}</option>)}
            </select></div>
          <DialogFooter className="gap-2">
            <Button type="button" variant="ghost" onClick={aoFechar}>Cancelar</Button>
            <Button type="submit" disabled={m.isPending}>Criar ação</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

