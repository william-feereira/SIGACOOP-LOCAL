/** Cliente da API do Django: mesma origem, cookie de sessão e token CSRF. */
export class ErroApi extends Error {
  constructor(public status: number, message: string, public codigo?: string, public campos?: Record<string, string[]>) {
    super(message);
  }
}

function csrf(): string {
  const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : '';
}

function mensagemDeCampos(dados: Record<string, unknown>): string {
  const primeira = Object.values(dados).find((v) => Array.isArray(v)) as string[] | undefined;
  return primeira?.[0] ?? 'Confira os campos e tente de novo.';
}

export async function api<T>(caminho: string, opcoes: { metodo?: string; corpo?: unknown } = {}): Promise<T> {
  const metodo = opcoes.metodo ?? (opcoes.corpo !== undefined ? 'POST' : 'GET');
  const resposta = await fetch(`/api${caminho}`, {
    method: metodo,
    credentials: 'same-origin',
    headers: {
      Accept: 'application/json',
      ...(metodo !== 'GET' ? { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() } : {}),
    },
    body: opcoes.corpo !== undefined ? JSON.stringify(opcoes.corpo) : undefined,
  });
  if (resposta.status === 204) return undefined as T;
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    if (dados.codigo === 'nao_autenticado' || dados.codigo === 'mfa') {
      const destino = `${dados.login}?next=${encodeURIComponent(location.pathname + location.search)}`;
      location.assign(destino);
    }
    const msg = typeof dados.detail === 'string' ? dados.detail : mensagemDeCampos(dados);
    throw new ErroApi(resposta.status, msg, dados.codigo, dados);
  }
  return dados as T;
}
