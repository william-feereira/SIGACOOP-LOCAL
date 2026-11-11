# SIGA Coop — regras para agentes

- Sistema único: **Django 5.2 + PostgreSQL**, rodando em VM Linux. Sem Supabase, sem Lovable, sem Node em produção.
- Escopo por unidade: toda consulta passa por `apps/core/access.py` (`filtrar_por_unidade`, `pode_ver_unidade`,
  `pode_gerir_unidade`). Registro fora do escopo responde 404.
- Perfis = Grupos do Django sincronizados em `apps/accounts/perfis.py` após o `migrate`.
- Mudança de estado com histórico e auditoria sempre dentro de `transaction.atomic()`.
- Regras de negócio no Python/banco (constraints). O navegador só pré-valida.
- Migrações versionadas em `apps/*/migrations/`; `makemigrations --check` precisa passar.
- Front-end: templates do Django + `static/css/siga.css`. Ícones só do sprite Lucide (`{% icone "nome" %}`);
  para adicionar, edite `scripts/gerar_icones.py`. JavaScript só local (sem CDN).
- Seguir o Prompt Mestre do projeto: plano antes de codar, etapas pequenas, checklist ao fim de cada etapa.
