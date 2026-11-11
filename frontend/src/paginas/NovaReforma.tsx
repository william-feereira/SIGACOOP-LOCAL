import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from '@tanstack/react-router';
import { useState, type FormEvent } from 'react';
import { CircleCheck, Plus, X } from 'lucide-react';
import { api, ErroApi } from '@/lib/api';
import { useEu } from '@/lib/eu';
import type { Pessoa, Reforma } from '@/lib/tipos';
import { Cabecalho } from '@/components/Comuns';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

/** Sugestão inicial, editável. A lista oficial de etapas de reforma de PA ainda será definida pela cooperativa. */
const SUGESTAO = [
  'Isolar e proteger a área', 'Retirada e demolição', 'Elétrica', 'Rede lógica e telefonia', 'Ar-condicionado',
  'Forro e pintura', 'Piso', 'Mobiliário', 'Comunicação visual', 'Segurança (alarme e CFTV)', 'Limpeza final', 'Vistoria e entrega',
];

const campo = 'flex flex-col gap-1 text-sm font-medium';

export function NovaReformaPagina() {
  const { data: eu } = useEu();
  const pessoas = useQuery({ queryKey: ['pessoas'], queryFn: () => api<Pessoa[]>('/pessoas/') });
  const qc = useQueryClient();
  const navegar = useNavigate();
  const [etapa, setEtapa] = useState<1 | 2 | 3>(1);
  const [dados, setDados] = useState({ unidade: '', titulo: '', objetivo: '', responsavel: '', inicio: '', fim_previsto: '', orcamento: '' });
  const [acoes, setAcoes] = useState<string[]>(SUGESTAO);
  const [nova, setNova] = useState('');
  const [erros, setErros] = useState<Record<string, string>>({});
  const unidades = eu?.unidades.filter((u) => u.pode_gerir) ?? [];

  const criar = useMutation({
    mutationFn: () => api<Reforma>('/reformas/', { corpo: {
      unidade: Number(dados.unidade), titulo: dados.titulo, objetivo: dados.objetivo,
      responsavel: dados.responsavel ? Number(dados.responsavel) : null, inicio: dados.inicio || null,
      fim_previsto: dados.fim_previsto || null, orcamento: dados.orcamento ? dados.orcamento.replace(/\./g, '').replace(',', '.') : null,
      acoes_iniciais: acoes,
    } }),
    onSuccess: (r) => { qc.invalidateQueries({ queryKey: ['reformas'] }); setCriada(r); setEtapa(3); },
    onError: (e) => {
      if (e instanceof ErroApi && e.campos) {
        setErros(Object.fromEntries(Object.entries(e.campos).filter(([, v]) => Array.isArray(v)).map(([k, v]) => [k, (v as string[])[0]])));
        setEtapa(1);
      } else setErros({ geral: e.message });
    },
  });
  const [criada, setCriada] = useState<Reforma | null>(null);
  const set = (k: keyof typeof dados) => (e: { target: { value: string } }) => setDados((d) => ({ ...d, [k]: e.target.value }));

  function avancar(e: FormEvent) {
    e.preventDefault();
    const novos: Record<string, string> = {};
    if (!dados.unidade) novos.unidade = 'Escolha o PA.';
    if (!dados.titulo.trim()) novos.titulo = 'Dê um nome para a reforma.';
    if (dados.inicio && dados.fim_previsto && dados.fim_previsto < dados.inicio) novos.fim_previsto = 'A previsão de término precisa ser depois do início.';
    setErros(novos);
    if (!Object.keys(novos).length) setEtapa(2);
  }
  const erro = (k: string) => erros[k] && <p id={`${k}-erro`} className="text-sm font-semibold text-destructive">{erros[k]}</p>;
  const descr = (k: string) => (erros[k] ? { 'aria-invalid': true, 'aria-describedby': `${k}-erro` } : {});

  if (etapa === 3 && criada) {
    return (
      <div className="mx-auto max-w-lg py-10 text-center">
        <CircleCheck className="mx-auto size-14 text-success" aria-hidden />
        <h1 className="mt-4 text-2xl font-bold text-primary">Reforma aberta</h1>
        <p className="mt-2 text-muted-foreground"><b>{criada.codigo}</b> · {criada.titulo}<br />{acoes.length} ações já estão em "A fazer". Agora é só distribuir os responsáveis.</p>
        <Button className="mt-6" onClick={() => navegar({ to: '/reformas/$id', params: { id: String(criada.id) } })}>Abrir o quadro</Button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <Cabecalho sobretitulo={`Etapa ${etapa} de 2`} titulo="Nova reforma" descricao={etapa === 1 ? 'Dados básicos da obra.' : 'Ações que vão para o quadro. Ajuste à vontade, dá para mudar depois.'} />
      {erros.geral && <p role="alert" className="mb-4 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm">{erros.geral}</p>}
      {etapa === 1 ? (
        <form onSubmit={avancar} noValidate className="grid gap-4 rounded-xl border bg-card p-5 shadow-card">
          <label className={campo}>PA *
            <select value={dados.unidade} onChange={set('unidade')} className="h-11 rounded-md border border-input bg-card px-3" {...descr('unidade')}>
              <option value="">Escolha o PA</option>
              {unidades.map((u) => <option key={u.id} value={u.id}>{u.code} · {u.name}</option>)}
            </select>{erro('unidade')}
          </label>
          <label className={campo}>Nome da reforma *<Input value={dados.titulo} onChange={set('titulo')} maxLength={160} placeholder="Ex.: Reforma da recepção e caixas" {...descr('titulo')} />{erro('titulo')}</label>
          <label className={campo}>Objetivo<Textarea value={dados.objetivo} onChange={set('objetivo')} rows={3} /></label>
          <label className={campo}>Responsável interno
            <select value={dados.responsavel} onChange={set('responsavel')} className="h-11 rounded-md border border-input bg-card px-3">
              <option value="">Definir depois</option>
              {pessoas.data?.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
            </select>
          </label>
          <div className="grid gap-4 sm:grid-cols-3">
            <label className={campo}>Início<Input type="date" value={dados.inicio} onChange={set('inicio')} /></label>
            <label className={campo}>Previsão de término<Input type="date" value={dados.fim_previsto} onChange={set('fim_previsto')} {...descr('fim_previsto')} />{erro('fim_previsto')}</label>
            <label className={campo}>Orçamento (R$)<Input inputMode="decimal" value={dados.orcamento} onChange={set('orcamento')} placeholder="0,00" />{erro('orcamento')}</label>
          </div>
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="outline" asChild><Link to="/reformas">Cancelar</Link></Button>
            <Button type="submit">Continuar</Button>
          </div>
        </form>
      ) : (
        <div className="grid gap-4 rounded-xl border bg-card p-5 shadow-card">
          <ul className="divide-y" aria-label="Ações iniciais">
            {acoes.map((a, i) => (
              <li key={`${a}-${i}`} className="flex items-center justify-between gap-2 py-1.5">
                <span>{a}</span>
                <button type="button" className="grid size-11 place-items-center rounded-md hover:bg-muted" aria-label={`Remover ${a}`} onClick={() => setAcoes((l) => l.filter((_, j) => j !== i))}><X className="size-4" aria-hidden /></button>
              </li>
            ))}
            {acoes.length === 0 && <li className="py-3 text-muted-foreground">Sem ações. O quadro começa vazio.</li>}
          </ul>
          <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (nova.trim()) { setAcoes((l) => [...l, nova.trim()]); setNova(''); } }}>
            <label className="sr-only" htmlFor="nova-acao">Nova ação</label>
            <Input id="nova-acao" value={nova} onChange={(e) => setNova(e.target.value)} placeholder="Adicionar outra ação" maxLength={160} />
            <Button type="submit" variant="outline" aria-label="Adicionar ação"><Plus className="size-4" aria-hidden /></Button>
          </form>
          <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
            <Button variant="outline" onClick={() => setEtapa(1)}>Voltar</Button>
            <Button onClick={() => criar.mutate()} disabled={criar.isPending}>{criar.isPending ? 'Abrindo…' : 'Abrir reforma'}</Button>
          </div>
        </div>
      )}
    </div>
  );
}
