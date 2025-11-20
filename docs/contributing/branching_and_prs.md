# Estrategia de ramas y Pull Requests (PR)

## Objetivo
Mantener `main` estable y siempre desplegable, con ramas cortas por cambio, PRs pequeños, CI verde y releases claros.

## Ramas
- `main`: estable, protegida.
- Ramas de trabajo (cortas):
  - `feat/<scope>`
  - `fix/<bug>`
  - `chore/<tarea>`
  - `docs/<área>`
  - `refactor/<módulo>`
  - `perf/<área>`
  - `test/<área>`
  - `ci/<pipeline>`
- Opcionales:
  - `hotfix/<incidente>`
  - `release/vX.Y`

## Flujo (fork → upstream)
1. Sincroniza `main`:
   ```bash
   git checkout main
   git pull --rebase
   git push origin main
   ```
2. Rama de trabajo:
   ```bash
   git checkout -b feat/<scope>
   ```
3. Commits (Convencional Commits):
   - `feat(normalizer): lowercase de severity`
   - `fix(parser): manejar quotes anidados`
4. Rebase frecuente:
   ```bash
   git fetch upstream
   git rebase upstream/main
   git push --force-with-lease
   ```
5. PR hacia `upstream/main`:
   - Título = `tipo(scope): resumen`
   - CI verde + review
   - “Squash and merge”
6. Post-merge:
   ```bash
   git checkout main
   git pull --rebase
   git push origin main
   ```

## Releases
- Tags directos en `main`: `vX.Y.Z`.
- Si se requiere estabilización: `release/vX.Y` hasta publicar `vX.Y.0`.

## Reglas de PR
- Pequeños y enfocados.
- CI obligatorio (tests/linters).
- Al menos 1 aprobación.
- Relacionar issues (`Closes #NNN`).
- “Squash and merge” por defecto.

## Protecciones de rama
- Prohibir push directo a `main`.
- Requerir PR, CI verde y 1+ review.
- Opcional: historia lineal.

## Buenas prácticas
- Ramas vivas < 5 días.
- Feature flags para evitar ramas largas.
- `--force-with-lease` si reescribes historia.
- Draft PR para feedback temprano.