import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';
import { ArrowRightLeft, CalendarDays, CircleAlert, Flag, Link2, Send, User } from 'lucide-react';
import { api, ErroApi } from '@/lib/api';
import type { AcaoDetalhe, ColunaId, Fornecedor, Pessoa, Registro } from '@/lib/tipos';
import { COLUNAS, ROTULO_COLUNA, ROTULO_PRIORIDADE } from '@/lib/tipos';
import { fmtData, fmtDataHora } from '@/lib/formato';
import { useAvisos } from '@/components/Avisos';
import { ErroCarregar, SeloColuna } from '@/components/Comuns';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';

const campoSelect = 'h-11 w-full rounded-md border border-input bg-card px-3';

/** Painel lateral do cartão: tudo que um terceiro precisa saber para continuar o trabalho. */
export function AcaoPainel({ acaoId, reformaId, aoFechar }: { acaoId: number | null; reformaId: number; aoFechar: () => void }) {
  return (
    <Sheet open={acaoId !== null} onOpenChange={(aberto) => !aberto && aoFechar()}>
      <SheetContent className="w-full sm:max-w-xl overflow-y-auto p-0">
        {acaoId !== null && <Conteudo acaoId={acaoId} reformaId={reformaId} />}
      </SheetContent>
    </Sheet>
  );
}

function Conteudo({ acaoId, reformaId }: { acaoId: number; reformaId: number }) {
  const qc = useQueryClient();
  const avisar = useAvisos();
  const q = useQuery({ queryKey: ['acao', acaoId], queryFn: () => api<AcaoDetalhe>(`/acoes/${acaoId}/`) });

  const atualizar = () => {
    qc.invalidateQueries({ queryKey: ['acao', acaoId] });
    qc.invalidateQueries({ queryKey: ['reforma', reformaId] });
    qc.invalidateQueries({ queryKey: ['linha', reformaId] });
  };
  const falhou = (e: unknown) => {
    avisar('erro', e instanceof Error ? e.message : 'Não foi possível salvar.');
    if (e instanceof ErroApi && e.codigo === 'conflito') atualizar();
  };

  if (q.isPending) return <div className="space-y-3 p-6"><Skeleton className="h-8 w-2/3" /><Skeleton className="h-24" /><Skeleton className="h-40" /></div>;
  if (q.isError) return <div className="p-6"><ErroCarregar erro={q.error} tentar={() => q.refetch()} /></div>;
  const a = q.data;

  return (
    <div className="flex flex-col">
      <SheetHeader className="border-b p-6 pr-12 text-left">
        <p className="text-sm text-muted-foreground">{a.reforma.codigo}</p>
        <SheetTitle className="text-xl text-primary">{a.titulo}</SheetTitle>
        <SheetDescription asChild>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <SeloColuna coluna={a.coluna} />
            <span className="inline-flex items-center gap-1 text-sm"><Flag className="size-4" aria-hidden />Prioridade {ROTULO_PRIORIDADE[a.prioridade].toLowerCase()}</span>
          </div>
        </SheetDescription>
      </SheetHeader>

      <div className="space-y-8 p-6">
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <Info icone={<User className="size-4" aria-hidden />} rotulo="Quem faz" valor={a.quem_faz} />
          <Info icone={<CalendarDays className="size-4" aria-hidden />} rotulo="Prazo"
            valor={a.prazo ? `${fmtData(a.prazo)}${a.atrasada ? ' (atrasada)' : ''}` : 'Sem prazo'} destaque={a.atrasada} />
          {a.depende_de && <Info icone={<Link2 className="size-4" aria-hidden />} rotulo="Depende de" valor={`${a.depende_de.titulo} (${ROTULO_COLUNA[a.depende_de.coluna]})`} />}
        </dl>
        {a.descricao && <p className="whitespace-pre-line text-sm">{a.descricao}</p>}
        {a.coluna === 'BLOQUEADA' && a.motivo_bloqueio && (
          <div className="flex gap-2 rounded-lg border border-warning/50 bg-warning/10 p-3 text-sm text-[#7a3d00]">
            <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden /><p><strong>Por que parou:</strong> {a.motivo_bloqueio}</p>
          </div>
        )}

        {a.pode_editar && <Mover acao={a} aoSalvar={atualizar} aoFalhar={falhou} />}
        {a.pode_editar && <Passar acao={a} aoSalvar={atualizar} aoFalhar={falhou} />}
        <Checklist acao={a} aoSalvar={atualizar} aoFalhar={falhou} />
        <Diario acao={a} aoSalvar={atualizar} aoFalhar={falhou} />
      </div>
    </div>
  );
}

type Secao = { acao: AcaoDetalhe; aoSalvar: () => void; aoFalhar: (e: unknown) => void };

function Info({ icone, rotulo, valor, destaque }: { icone: React.ReactNode; rotulo: string; valor: string; destaque?: boolean }) {
  return (
    <div className="flex gap-2">
      <span className="mt-0.5 text-muted-foreground">{icone}</span>
      <div><dt className="text-muted-foreground">{rotulo}</dt><dd className={destaque ? 'font-semibold text-destructive' : 'font-medium'}>{valor}</dd></div>
    </div>
  );
}

function Mover({ acao, aoSalvar, aoFalhar }: Secao) {
  const avisar = useAvisos();
  const [coluna, setColuna] = useState<ColunaId>(acao.coluna);
  const [motivo, setMotivo] = useState('');
  const m = useMutation({
    mutationFn: () => api(`/acoes/${acao.id}/mover/`, { corpo: { coluna, versao: acao.versao, motivo_bloqueio: motivo } }),
    onSuccess: () => { avisar('ok', `Movida para "${ROTULO_COLUNA[coluna]}".`); setMotivo(''); aoSalvar(); },
    onError: aoFalhar,
  });
  const enviar = (e: FormEvent) => { e.preventDefault(); if (coluna !== acao.coluna) m.mutate(); };
  return (
    <form onSubmit={enviar} className="space-y-3" aria-labelledby="t-mover">
      <h3 id="t-mover" className="font-semibold text-primary">Mudar etapa</h3>
      <div className="flex flex-col gap-2 sm:flex-row">
        <label className="sr-only" htmlFor="mover-para">Mover para</label>
        <select id="mover-para" className={campoSelect} value={coluna} onChange={(e) => setColuna(e.target.value as ColunaId)}>
          {COLUNAS.map((c) => <option key={c.id} value={c.id}>{c.rotulo}</option>)}
        </select>
        <Button type="submit" disabled={coluna === acao.coluna || m.isPending} className="sm:w-40"><ArrowRightLeft className="size-4" aria-hidden />Mover</Button>
      </div>
      {coluna === 'BLOQUEADA' && coluna !== acao.coluna && (
        <div className="space-y-1">
          <Label htmlFor="motivo">Por que vai parar? (obrigatório)</Label>
          <Textarea id="motivo" required value={motivo} onChange={(e) => setMotivo(e.target.value)} placeholder="Ex.: aguardando entrega do material elétrico" />
        </div>
      )}
    </form>
  );
}

function Passar({ acao, aoSalvar, aoFalhar }: Secao) {
  const avisar = useAvisos();
  const [aberto, setAberto] = useState(false);
  const [feito, setFeito] = useState('');
  const [falta, setFalta] = useState('');
  const [para, setPara] = useState('');
  const pessoas = useQuery({ queryKey: ['pessoas'], queryFn: () => api<Pessoa[]>('/pessoas/'), enabled: aberto });
  const fornecedores = useQuery({ queryKey: ['fornecedores'], queryFn: () => api<Fornecedor[]>('/fornecedores/'), enabled: aberto });
  const m = useMutation({
    mutationFn: () => {
      const [tipo, id] = para.split(':');
      return api(`/acoes/${acao.id}/passar/`, { corpo: { feito, o_que_falta: falta, versao: acao.versao,
        para_usuario: tipo === 'u' ? Number(id) : null, para_fornecedor: tipo === 'f' ? Number(id) : null } });
    },
    onSuccess: () => { avisar('ok', 'Passagem registrada. O próximo responsável já aparece no cartão.'); setAberto(false); setFeito(''); setFalta(''); setPara(''); aoSalvar(); },
    onError: aoFalhar,
  });
  if (!aberto) {
    return (
      <div className="rounded-lg border border-dashed p-4">
        <p className="text-sm text-muted-foreground">Terminou a sua parte e outra pessoa ou empresa continua?</p>
        <Button variant="outline" className="mt-3" onClick={() => setAberto(true)}><Send className="size-4" aria-hidden />Passar adiante</Button>
      </div>
    );
  }
  return (
    <form onSubmit={(e) => { e.preventDefault(); m.mutate(); }} className="space-y-3 rounded-lg border p-4" aria-labelledby="t-passar">
      <h3 id="t-passar" className="font-semibold text-primary">Passar adiante</h3>
      <div className="space-y-1"><Label htmlFor="feito">O que foi feito</Label>
        <Textarea id="feito" required value={feito} onChange={(e) => setFeito(e.target.value)} placeholder="Ex.: passagem dos cabos concluída no salão" /></div>
      <div className="space-y-1"><Label htmlFor="falta">O que falta (para quem continua)</Label>
        <Textarea id="falta" required value={falta} onChange={(e) => setFalta(e.target.value)} placeholder="Ex.: instalar tomadas e testar o quadro" /></div>
      <div className="space-y-1"><Label htmlFor="para">Quem continua</Label>
        <select id="para" required className={campoSelect} value={para} onChange={(e) => setPara(e.target.value)}>
          <option value="">Escolha…</option>
          <optgroup label="Pessoas">{pessoas.data?.map((p) => <option key={`u${p.id}`} value={`u:${p.id}`}>{p.nome}</option>)}</optgroup>
          <optgroup label="Empresas terceirizadas">{fornecedores.data?.map((f) => <option key={`f${f.id}`} value={`f:${f.id}`}>{f.nome}{f.especialidade ? ` (${f.especialidade})` : ''}</option>)}</optgroup>
        </select></div>
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="ghost" onClick={() => setAberto(false)}>Cancelar</Button>
        <Button type="submit" disabled={m.isPending}>Registrar passagem</Button>
      </div>
    </form>
  );
}

function Checklist({ acao, aoSalvar, aoFalhar }: Secao) {
  const [novo, setNovo] = useState('');
  const marcar = useMutation({ mutationFn: (p: { id: number; feito: boolean }) => api(`/checklist/${p.id}/`, { metodo: 'PATCH', corpo: { feito: p.feito } }), onSuccess: aoSalvar, onError: aoFalhar });
  const add = useMutation({ mutationFn: () => api(`/acoes/${acao.id}/checklist/`, { corpo: { texto: novo } }), onSuccess: () => { setNovo(''); aoSalvar(); }, onError: aoFalhar });
  const feitos = acao.checklist.filter((i) => i.feito).length;
  return (
    <section aria-labelledby="t-check" className="space-y-2">
      <h3 id="t-check" className="font-semibold text-primary">Checklist {acao.checklist.length > 0 && <span className="font-normal text-muted-foreground tabular-nums">({feitos}/{acao.checklist.length})</span>}</h3>
      {acao.checklist.length === 0 && <p className="text-sm text-muted-foreground">Sem itens ainda.</p>}
      <ul className="space-y-1">
        {acao.checklist.map((i) => (
          <li key={i.id}>
            <label className="flex min-h-11 items-center gap-3 rounded-md px-2 hover:bg-muted/60">
              <Checkbox checked={i.feito} disabled={!acao.pode_editar || marcar.isPending} onCheckedChange={(v) => marcar.mutate({ id: i.id, feito: v === true })} />
              <span className={`text-sm ${i.feito ? 'text-muted-foreground line-through' : ''}`}>{i.texto}</span>
              {i.feito && i.feito_por && <span className="ml-auto text-xs text-muted-foreground">{i.feito_por.nome}</span>}
            </label>
          </li>
        ))}
      </ul>
      {acao.pode_editar && (
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (novo.trim()) add.mutate(); }}>
          <label htmlFor="novo-item" className="sr-only">Novo item do checklist</label>
          <Input id="novo-item" value={novo} onChange={(e) => setNovo(e.target.value)} placeholder="Novo item" maxLength={200} />
          <Button type="submit" variant="outline" disabled={add.isPending}>Adicionar</Button>
        </form>
      )}
    </section>
  );
}

function Diario({ acao, aoSalvar, aoFalhar }: Secao) {
  const avisar = useAvisos();
  const [texto, setTexto] = useState('');
  const m = useMutation({
    mutationFn: () => api(`/acoes/${acao.id}/andamento/`, { corpo: { texto } }),
    onSuccess: () => { setTexto(''); avisar('ok', 'Andamento registrado.'); aoSalvar(); },
    onError: aoFalhar,
  });
  return (
    <section aria-labelledby="t-diario" className="space-y-3">
      <h3 id="t-diario" className="font-semibold text-primary">Diário da ação</h3>
      {acao.pode_editar && (
        <form className="space-y-2" onSubmit={(e) => { e.preventDefault(); if (texto.trim()) m.mutate(); }}>
          <Label htmlFor="andamento">Registrar andamento</Label>
          <Textarea id="andamento" value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="O que aconteceu hoje nesta ação?" maxLength={4000} />
          <Button type="submit" disabled={m.isPending || !texto.trim()}>Registrar</Button>
        </form>
      )}
      <ListaRegistros registros={acao.registros} />
    </section>
  );
}

export function ListaRegistros({ registros, mostrarAcao }: { registros: Registro[]; mostrarAcao?: boolean }) {
  if (registros.length === 0) return <p className="text-sm text-muted-foreground">Nada registrado ainda.</p>;
  return (
    <ol className="relative space-y-4 border-l pl-5">
      {registros.map((r) => (
        <li key={r.id} className="relative">
          <span className="absolute -left-[26px] top-1.5 size-2.5 rounded-full bg-primary ring-4 ring-background" aria-hidden />
          <p className="text-sm"><strong>{r.autor.nome}</strong> · {r.tipo_rotulo}
            {r.para_coluna && r.de_coluna && <> de <em>{ROTULO_COLUNA[r.de_coluna as ColunaId]}</em> para <em>{ROTULO_COLUNA[r.para_coluna as ColunaId]}</em></>}
            {r.passado_para && <> para <strong>{r.passado_para.nome}</strong></>}
          </p>
          {mostrarAcao && <p className="text-xs font-medium text-brand-teal-ink">{r.acao.titulo}</p>}
          {r.texto && <p className="mt-1 whitespace-pre-line text-sm">{r.texto}</p>}
          {r.o_que_falta && <p className="mt-1 text-sm"><span className="font-semibold">Falta:</span> {r.o_que_falta}</p>}
          <p className="mt-1 text-xs text-muted-foreground"><time dateTime={r.criado_em}>{fmtDataHora(r.criado_em)}</time></p>
        </li>
      ))}
    </ol>
  );
}
