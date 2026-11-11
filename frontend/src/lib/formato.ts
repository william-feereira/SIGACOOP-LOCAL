const dataHora = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'America/Sao_Paulo' });
const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

/** "2026-12-18" (data do banco, sem fuso) → "18/12/2026". */
export function fmtData(iso: string | null | undefined): string {
  if (!iso) return '';
  const [a, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}/${a}`;
}
export const fmtDataHora = (iso: string) => dataHora.format(new Date(iso));
export const fmtMoeda = (v: string | number | null) => (v == null || v === '' ? '' : moeda.format(Number(v)));
