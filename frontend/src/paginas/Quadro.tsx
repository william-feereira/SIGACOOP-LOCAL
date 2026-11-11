import { DndContext, DragOverlay, KeyboardSensor, PointerSensor, closestCorners, useDroppable, useSensor, useSensors, type DragEndEvent, type DragStartEvent } from '@dnd-kit/core';
import { SortableContext, sortableKeyboardCoordinates, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useState } from 'react';
import { CalendarDays, CircleAlert, GripVertical, Link2, ListChecks, User } from 'lucide-react';
import type { Acao, ColunaId } from '@/lib/tipos';
import { COLUNAS } from '@/lib/tipos';
import { porColuna } from '@/lib/kanban';
import { fmtData } from '@/lib/formato';

type Props = { acoes: Acao[]; podeEditar: boolean; aoAbrir: (id: number) => void; aoMover: (id: number, coluna: ColunaId, indice: number) => void };

const anuncios = {
  onDragStart: () => 'Cartão selecionado. Use as setas para mover e espaço para soltar.',
  onDragOver: () => '',
  onDragEnd: () => 'Cartão solto.',
  onDragCancel: () => 'Movimento cancelado.',
};

export function Quadro({ acoes, podeEditar, aoAbrir, aoMover }: Props) {
  const [arrastando, setArrastando] = useState<Acao | null>(null);
  const [colunaMovel, setColunaMovel] = useState<ColunaId>('EM_ANDAMENTO');
  const sensores = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  function colunaDe(id: string | number): ColunaId | undefined {
    if (typeof id === 'string' && id.startsWith('coluna-')) return id.slice(7) as ColunaId;
    return acoes.find((a) => a.id === id)?.coluna;
  }
  function inicio(e: DragStartEvent) { setArrastando(acoes.find((a) => a.id === e.active.id) ?? null); }
  function fim(e: DragEndEvent) {
    setArrastando(null);
    if (!e.over) return;
    const destino = colunaDe(e.over.id);
    if (!destino) return;
    const lista = porColuna(acoes, destino).filter((a) => a.id !== e.active.id);
    const indice = typeof e.over.id === 'number' ? Math.max(0, lista.findIndex((a) => a.id === e.over!.id)) : lista.length;
    const atual = acoes.find((a) => a.id === e.active.id)!;
    if (atual.coluna === destino && porColuna(acoes, destino).findIndex((a) => a.id === atual.id) === indice) return;
    aoMover(Number(e.active.id), destino, indice);
  }

  const contagem = (c: ColunaId) => acoes.filter((a) => a.coluna === c).length;
  return (
    <>
      {/* Celular: uma coluna por vez, escolhida nas abas */}
      <div className="md:hidden mb-3 -mx-4 px-4 overflow-x-auto">
        <div role="tablist" aria-label="Colunas do quadro" className="flex gap-2 w-max">
          {COLUNAS.map((c) => (
            <button key={c.id} role="tab" aria-selected={colunaMovel === c.id} onClick={() => setColunaMovel(c.id)}
              className={`h-11 rounded-full border px-4 text-sm whitespace-nowrap ${colunaMovel === c.id ? 'bg-primary text-primary-foreground border-primary' : 'bg-card'}`}>
              {c.rotulo} <span className="tabular-nums opacity-80">({contagem(c.id)})</span>
            </button>
          ))}
        </div>
      </div>
      <DndContext sensors={sensores} collisionDetection={closestCorners} onDragStart={inicio} onDragEnd={fim} onDragCancel={() => setArrastando(null)}
        accessibility={{ announcements: anuncios, screenReaderInstructions: { draggable: 'Para mover, pressione espaço, use as setas e espaço de novo para soltar. Ou abra o cartão e use "Mover para".' } }}>
        <div className="grid gap-3 md:grid-cols-[repeat(5,minmax(196px,1fr))] md:overflow-x-auto pb-2">
          {COLUNAS.map((c) => (
            <Coluna key={c.id} id={c.id} rotulo={c.rotulo} acoes={porColuna(acoes, c.id)} podeEditar={podeEditar} aoAbrir={aoAbrir}
              oculta={colunaMovel !== c.id} />
          ))}
        </div>
        <DragOverlay>{arrastando && <Cartao acao={arrastando} sobreposto />}</DragOverlay>
      </DndContext>
    </>
  );
}

function Coluna({ id, rotulo, acoes, podeEditar, aoAbrir, oculta }: { id: ColunaId; rotulo: string; acoes: Acao[]; podeEditar: boolean; aoAbrir: (id: number) => void; oculta: boolean }) {
  const { setNodeRef, isOver } = useDroppable({ id: `coluna-${id}`, disabled: !podeEditar });
  return (
    <section aria-label={`${rotulo}, ${acoes.length} ações`} className={`${oculta ? 'hidden md:flex' : 'flex'} min-w-0 flex-col rounded-xl border bg-muted/60 p-2 ${isOver ? 'ring-2 ring-primary/40' : ''}`}>
      <h2 className="hidden md:flex items-center justify-between px-2 py-2 text-sm font-semibold text-primary">
        {rotulo}<span className="rounded-full bg-card px-2 text-xs tabular-nums text-muted-foreground">{acoes.length}</span>
      </h2>
      <div ref={setNodeRef} className="flex min-h-24 flex-1 flex-col gap-2">
        <SortableContext id={id} items={acoes.map((a) => a.id)} strategy={verticalListSortingStrategy}>
          {acoes.map((a) => <CartaoArrastavel key={a.id} acao={a} podeEditar={podeEditar} aoAbrir={aoAbrir} />)}
        </SortableContext>
        {acoes.length === 0 && <p className="px-2 py-6 text-center text-sm text-muted-foreground">Nenhuma ação aqui.</p>}
      </div>
    </section>
  );
}

function CartaoArrastavel({ acao, podeEditar, aoAbrir }: { acao: Acao; podeEditar: boolean; aoAbrir: (id: number) => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: acao.id, disabled: !podeEditar });
  return (
    <div ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition }} className={isDragging ? 'opacity-40' : ''}>
      <Cartao acao={acao} aoAbrir={() => aoAbrir(acao.id)} alca={podeEditar ? { ...attributes, ...listeners } : undefined} />
    </div>
  );
}

export function Cartao({ acao, aoAbrir, alca, sobreposto }: { acao: Acao; aoAbrir?: () => void; alca?: Record<string, unknown>; sobreposto?: boolean }) {
  const bloqueada = acao.coluna === 'BLOQUEADA';
  return (
    <article className={`group relative rounded-lg border bg-card p-3 shadow-sm ${bloqueada ? 'border-warning border-l-4' : ''} ${sobreposto ? 'shadow-elevated rotate-1' : ''}`}>
      <div className="flex items-start gap-1">
        <button type="button" onClick={aoAbrir} className="min-h-11 flex-1 text-left font-medium leading-snug after:absolute after:inset-0 after:content-['']">
          {acao.titulo}
        </button>
        {alca && (
          <button type="button" {...alca} aria-label={`Mover "${acao.titulo}"`} className="relative z-10 -mr-1 grid h-11 w-8 shrink-0 cursor-grab place-items-center rounded text-muted-foreground hover:bg-muted active:cursor-grabbing touch-none">
            <GripVertical className="size-4" aria-hidden />
          </button>
        )}
      </div>
      {bloqueada && acao.motivo_bloqueio && (
        <p className="mt-1 flex gap-1 text-sm text-[#7a3d00]"><CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden /><span className="line-clamp-2">{acao.motivo_bloqueio}</span></p>
      )}
      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
        <li className="flex items-center gap-1"><User className="size-3.5" aria-hidden /><span className="truncate">{acao.quem_faz}</span></li>
        {acao.prazo && <li className={`flex items-center gap-1 ${acao.atrasada ? 'font-semibold text-destructive' : ''}`}><CalendarDays className="size-3.5" aria-hidden />{acao.atrasada ? 'Atrasada · ' : ''}{fmtData(acao.prazo)}</li>}
        {acao.depende_de && acao.depende_de.coluna !== 'CONCLUIDA' && <li className="flex items-center gap-1"><Link2 className="size-3.5" aria-hidden /><span className="truncate">Depois de: {acao.depende_de.titulo}</span></li>}
        {!!acao.checklist_total && <li className="flex items-center gap-1"><ListChecks className="size-3.5" aria-hidden />{acao.checklist_feitos}/{acao.checklist_total}</li>}
      </ul>
    </article>
  );
}
