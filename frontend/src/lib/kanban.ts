import type { Acao, ColunaId } from './tipos';

export function porColuna(acoes: Acao[], coluna: ColunaId): Acao[] {
  return acoes.filter((a) => a.coluna === coluna).sort((a, b) => a.posicao - b.posicao || a.id - b.id);
}

/** Move a ação para `coluna` na posição `indice` e renumera as colunas afetadas (atualização otimista). */
export function moverLocal(acoes: Acao[], id: number, coluna: ColunaId, indice: number): Acao[] {
  const alvo = acoes.find((a) => a.id === id);
  if (!alvo) return acoes;
  const outras = acoes.filter((a) => a.id !== id);
  const destino = porColuna(outras, coluna);
  destino.splice(Math.max(0, Math.min(indice, destino.length)), 0, { ...alvo, coluna });
  const posicoes = new Map(destino.map((a, p) => [a.id, p]));
  if (alvo.coluna !== coluna) porColuna(outras, alvo.coluna).forEach((a, p) => posicoes.set(a.id, p));
  return [...outras, { ...alvo, coluna }].map((a) => (posicoes.has(a.id) ? { ...a, posicao: posicoes.get(a.id)! } : a));
}
