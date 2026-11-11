import { describe, expect, it } from 'vitest';
import { moverLocal, porColuna } from './kanban';
import type { Acao, ColunaId } from './tipos';

const acao = (id: number, coluna: ColunaId, posicao: number) => ({ id, coluna, posicao, titulo: `A${id}` }) as Acao;
const titulos = (lista: Acao[], c: ColunaId) => porColuna(lista, c).map((a) => a.titulo);

describe('moverLocal', () => {
  const base = [acao(1, 'A_FAZER', 0), acao(2, 'A_FAZER', 1), acao(3, 'A_FAZER', 2), acao(4, 'EM_ANDAMENTO', 0)];

  it('reordena dentro da mesma coluna', () => {
    expect(titulos(moverLocal(base, 3, 'A_FAZER', 0), 'A_FAZER')).toEqual(['A3', 'A1', 'A2']);
  });

  it('move para outra coluna e fecha o buraco na origem', () => {
    const r = moverLocal(base, 1, 'EM_ANDAMENTO', 1);
    expect(titulos(r, 'EM_ANDAMENTO')).toEqual(['A4', 'A1']);
    expect(porColuna(r, 'A_FAZER').map((a) => a.posicao)).toEqual([0, 1]);
  });

  it('limita o índice ao tamanho da coluna', () => {
    expect(titulos(moverLocal(base, 2, 'CONCLUIDA', 99), 'CONCLUIDA')).toEqual(['A2']);
  });
});
