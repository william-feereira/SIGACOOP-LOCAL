import type { ReactNode } from 'react';
import { CircleAlert } from 'lucide-react';
import type { ColunaId } from '@/lib/tipos';
import { ROTULO_COLUNA } from '@/lib/tipos';

export function Cabecalho({ titulo, descricao, acao, sobretitulo }: { titulo: string; descricao?: ReactNode; acao?: ReactNode; sobretitulo?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        {sobretitulo && <p className="mb-1 text-sm font-semibold text-brand-teal-ink">{sobretitulo}</p>}
        <h1 className="text-2xl sm:text-3xl font-bold text-primary">{titulo}</h1>
        {descricao && <p className="mt-1 text-muted-foreground">{descricao}</p>}
      </div>
      {acao && <div className="shrink-0 [&>*]:w-full sm:[&>*]:w-auto">{acao}</div>}
    </header>
  );
}

export function ErroCarregar({ erro, tentar }: { erro: unknown; tentar?: () => void }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4">
      <CircleAlert className="size-5 text-destructive shrink-0" aria-hidden />
      <div className="text-sm">
        <p className="font-semibold">Não foi possível carregar.</p>
        <p className="text-muted-foreground">{erro instanceof Error ? erro.message : 'Verifique a conexão.'}</p>
        {tentar && <button className="mt-2 underline min-h-11" onClick={tentar}>Tentar de novo</button>}
      </div>
    </div>
  );
}

const COR_COLUNA: Record<ColunaId, string> = {
  A_FAZER: 'bg-muted text-foreground border-border',
  EM_ANDAMENTO: 'bg-info/10 text-[#0d4f8b] border-info/30',
  BLOQUEADA: 'bg-warning/15 text-[#7a3d00] border-warning/40',
  VALIDACAO: 'bg-accent text-accent-foreground border-brand-teal/30',
  CONCLUIDA: 'bg-success/10 text-success border-success/30',
};
export function SeloColuna({ coluna }: { coluna: ColunaId }) {
  return <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold whitespace-nowrap ${COR_COLUNA[coluna]}`}>{ROTULO_COLUNA[coluna]}</span>;
}

export function BarraProgresso({ valor, rotulo }: { valor: number; rotulo: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm"><span className="text-muted-foreground">{rotulo}</span><span className="font-semibold tabular-nums">{valor}%</span></div>
      <div className="h-2 rounded-full bg-muted" role="progressbar" aria-valuenow={valor} aria-valuemin={0} aria-valuemax={100} aria-label={rotulo}>
        <div className="h-2 rounded-full bg-primary transition-[width]" style={{ width: `${valor}%` }} />
      </div>
    </div>
  );
}
