import { Link, Outlet, useRouterState } from '@tanstack/react-router';
import { useState, type ComponentType } from 'react';
import { BarChart3, Boxes, Car, ClipboardList, FilePenLine, HardHat, House, LogOut, Menu, Plane, Settings, X } from 'lucide-react';
import icone from '@/assets/siga-icon.png';
import { useEu } from '@/lib/eu';
import { Skeleton } from '@/components/ui/skeleton';

type Item = { rotulo: string; para: string; Icone: ComponentType<{ className?: string }>; spa?: boolean; mostrar?: boolean };

function csrf() {
  return decodeURIComponent(document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)?.[1] ?? '');
}

function Navegacao({ aoNavegar }: { aoNavegar?: () => void }) {
  const { data: eu } = useEu();
  const caminho = useRouterState({ select: (s) => s.location.pathname });
  const secoes: [string, Item[]][] = [
    ['Início', [
      { rotulo: 'Visão geral', para: '/', Icone: House, spa: true },
      { rotulo: 'Solicitações', para: '/solicitacoes/', Icone: ClipboardList },
    ]],
    ['Operação', [
      { rotulo: 'Reformas dos PAs', para: '/reformas', Icone: HardHat, spa: true },
      { rotulo: 'Ativos e patrimônio', para: '/ativos/', Icone: Boxes, mostrar: eu?.permissoes.ativos },
      { rotulo: 'Frota', para: '/frota/', Icone: Car, mostrar: eu?.permissoes.frota },
      { rotulo: 'Viagens', para: '/viagens/', Icone: Plane },
    ]],
    ['Gestão', [
      { rotulo: 'Contratos e fornecedores', para: '/contratos/', Icone: FilePenLine, mostrar: eu?.permissoes.contratos },
      { rotulo: 'Indicadores', para: '/analytics/', Icone: BarChart3 },
      { rotulo: 'Administração', para: '/admin/', Icone: Settings, mostrar: eu?.staff },
    ]],
  ];
  const classe = (ativo: boolean) =>
    `flex min-h-11 items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${ativo ? 'bg-sidebar-primary/20 text-white shadow-[inset_3px_0_0_var(--brand-teal)]' : 'text-sidebar-foreground hover:bg-white/10'}`;
  return (
    <nav aria-label="Menu principal" className="space-y-4">
      {secoes.map(([titulo, itens]) => (
        <div key={titulo}>
          <p className="px-3 mb-1 text-xs uppercase tracking-wider text-sidebar-foreground/60">{titulo}</p>
          <ul className="space-y-0.5">
            {itens.filter((i) => i.mostrar !== false).map(({ rotulo, para, Icone, spa }) => {
              const ativo = spa && (para === '/' ? caminho === '/' : caminho.startsWith(para));
              return (
                <li key={para}>
                  {spa ? (
                    <Link to={para} onClick={aoNavegar} className={classe(!!ativo)} aria-current={ativo ? 'page' : undefined}>
                      <Icone className="size-5 shrink-0" aria-hidden />{rotulo}
                    </Link>
                  ) : (
                    <a href={para} className={classe(false)}><Icone className="size-5 shrink-0" aria-hidden />{rotulo}</a>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function Usuario() {
  const { data: eu, isLoading } = useEu();
  if (isLoading || !eu) return <Skeleton className="h-10 bg-white/10" />;
  return (
    <div className="flex items-center justify-between gap-2 border-t border-sidebar-border pt-3">
      <div className="min-w-0 text-sm">
        <p className="truncate text-white">{eu.nome}</p>
        <p className="truncate text-xs text-sidebar-foreground/70">{eu.perfis.join(', ') || 'Sem perfil'}</p>
      </div>
      <form method="post" action={eu.logout}>
        <input type="hidden" name="csrfmiddlewaretoken" value={csrf()} />
        <button type="submit" className="grid size-11 place-items-center rounded-lg text-sidebar-foreground hover:bg-white/10" aria-label="Sair do SIGA">
          <LogOut className="size-5" aria-hidden />
        </button>
      </form>
    </div>
  );
}

function Marca() {
  return (
    <Link to="/" className="flex items-center gap-3 px-2 text-white">
      <img src={icone} alt="" width={36} height={36} className="rounded-lg" />
      <span className="text-xl"><b className="font-extrabold">SIGA</b> Coop</span>
    </Link>
  );
}

export function AppShell() {
  const [aberto, setAberto] = useState(false);
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_minmax(0,1fr)]">
      <a href="#conteudo" className="skip-to-content">Ir para o conteúdo</a>
      <aside className="hidden lg:flex sticky top-0 h-screen flex-col gap-5 bg-sidebar px-3 py-6">
        <Marca />
        <div className="flex-1 overflow-y-auto"><Navegacao /></div>
        <Usuario />
      </aside>
      <header className="lg:hidden sticky top-0 z-40 flex items-center justify-between bg-sidebar px-3 py-2">
        <Marca />
        <button type="button" className="grid size-11 place-items-center rounded-lg text-white" aria-expanded={aberto} aria-controls="menu-movel"
          aria-label={aberto ? 'Fechar menu' : 'Abrir menu'} onClick={() => setAberto((v) => !v)}>
          {aberto ? <X aria-hidden /> : <Menu aria-hidden />}
        </button>
      </header>
      {aberto && (
        <div id="menu-movel" className="lg:hidden fixed inset-x-0 top-[60px] bottom-0 z-40 overflow-y-auto bg-sidebar px-3 pb-6 pt-2 space-y-4">
          <Navegacao aoNavegar={() => setAberto(false)} />
          <Usuario />
        </div>
      )}
      <main id="conteudo" tabIndex={-1} className="min-w-0 px-4 py-5 sm:px-8 sm:py-8 outline-none">
        <Outlet />
      </main>
    </div>
  );
}
