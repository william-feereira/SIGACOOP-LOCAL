export type Pessoa = { id: number; nome: string };
export type Fornecedor = { id: number; nome: string; especialidade: string };
export type Unidade = { id: number; code: string; name: string; pode_gerir?: boolean };
export type ColunaId = 'A_FAZER' | 'EM_ANDAMENTO' | 'BLOQUEADA' | 'VALIDACAO' | 'CONCLUIDA';
export type Prioridade = 'BAIXA' | 'NORMAL' | 'ALTA' | 'URGENTE';

export type Eu = {
  id: number; usuario: string; nome: string; perfis: string[]; admin: boolean; staff: boolean;
  unidades: Unidade[]; permissoes: { ativos: boolean; frota: boolean; contratos: boolean }; logout: string;
};

export type Progresso = { total: number; concluidas: number; bloqueadas: number; atrasadas: number; percentual: number };

export type Reforma = {
  id: number; codigo: string; titulo: string; objetivo: string; situacao: string; situacao_rotulo: string;
  unidade: Unidade; responsavel: Pessoa | null; inicio: string | null; fim_previsto: string | null;
  orcamento: string | null; progresso: Progresso; pode_editar: boolean;
};

export type Acao = {
  id: number; titulo: string; descricao: string; coluna: ColunaId; posicao: number; prioridade: Prioridade;
  prazo: string | null; atrasada: boolean; responsavel: Pessoa | null; fornecedor: Fornecedor | null; quem_faz: string;
  depende_de: { id: number; titulo: string; coluna: ColunaId } | null; motivo_bloqueio: string; versao: number;
  checklist_total: number | null; checklist_feitos: number | null;
};

export type ReformaDetalhe = Reforma & { colunas: { id: ColunaId; rotulo: string }[]; acoes: Acao[] };

export type Registro = {
  id: number; tipo: string; tipo_rotulo: string; texto: string; o_que_falta: string; de_coluna: string; para_coluna: string;
  autor: Pessoa; criado_em: string; passado_para: (Pessoa | Fornecedor) | null; acao: { id: number; titulo: string };
};

export type AcaoDetalhe = Acao & {
  pode_editar: boolean; reforma: { id: number; codigo: string; titulo: string };
  checklist: { id: number; texto: string; feito: boolean; feito_por: Pessoa | null; feito_em: string | null }[];
  registros: Registro[];
};

export const COLUNAS: { id: ColunaId; rotulo: string }[] = [
  { id: 'A_FAZER', rotulo: 'A fazer' },
  { id: 'EM_ANDAMENTO', rotulo: 'Em andamento' },
  { id: 'BLOQUEADA', rotulo: 'Pausada/Bloqueada' },
  { id: 'VALIDACAO', rotulo: 'Em validação' },
  { id: 'CONCLUIDA', rotulo: 'Concluída' },
];
export const ROTULO_COLUNA = Object.fromEntries(COLUNAS.map((c) => [c.id, c.rotulo])) as Record<ColunaId, string>;
export const ROTULO_PRIORIDADE: Record<Prioridade, string> = { BAIXA: 'Baixa', NORMAL: 'Normal', ALTA: 'Alta', URGENTE: 'Urgente' };
