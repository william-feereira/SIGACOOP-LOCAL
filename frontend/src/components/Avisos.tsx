import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
import { CircleAlert, CircleCheck, X } from 'lucide-react';

type Aviso = { id: number; tipo: 'ok' | 'erro'; texto: string };
const Ctx = createContext<(tipo: Aviso['tipo'], texto: string) => void>(() => {});

/** Avisos curtos (sucesso/erro) anunciados por leitor de tela. Sem CSS injetado, compatível com a CSP. */
export function AvisosProvider({ children }: { children: ReactNode }) {
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const avisar = useCallback((tipo: Aviso['tipo'], texto: string) => {
    const id = Date.now() + Math.random();
    setAvisos((a) => [...a.slice(-2), { id, tipo, texto }]);
    setTimeout(() => setAvisos((a) => a.filter((x) => x.id !== id)), tipo === 'erro' ? 8000 : 4000);
  }, []);
  return (
    <Ctx.Provider value={avisar}>
      {children}
      <div className="fixed bottom-4 right-4 left-4 sm:left-auto z-[60] flex flex-col gap-2 sm:w-96" aria-live="polite" role="status">
        {avisos.map((a) => (
          <div key={a.id} className={`flex items-start gap-3 rounded-lg border p-3 shadow-card bg-card ${a.tipo === 'erro' ? 'border-destructive/40' : 'border-success/40'}`}>
            {a.tipo === 'erro' ? <CircleAlert className="size-5 text-destructive shrink-0" aria-hidden /> : <CircleCheck className="size-5 text-success shrink-0" aria-hidden />}
            <p className="text-sm flex-1">{a.texto}</p>
            <button type="button" className="size-8 -m-1 grid place-items-center rounded" aria-label="Fechar aviso" onClick={() => setAvisos((x) => x.filter((y) => y.id !== a.id))}>
              <X className="size-4" aria-hidden />
            </button>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
export const useAvisos = () => useContext(Ctx);
