# Integración con api-anything

[`api-anything`](https://github.com/anthropics/api-anything) aprende sitios web y
los expone como operaciones verificables (`call`, `verify`, `result`). SIF Chile
no necesita aprendizaje: el contrato estático ya son GET con ids estables, así
que la spec se **genera** desde `docs/api/v2/` y se verifica en CI.

| Archivo | Qué es |
|---|---|
| `sif-chile.json` | Spec generada: 6 operaciones de lectura (catalog, schema, partitions, queries, resultados, resultado). |
| `sif-chile.md` | Notas para quien llama (formato de ids, qué hacer con un 404). |
| `etl/` | Experimento de ingesta HTML (CMF/SPensiones) con fixtures y ciclo deriva→reparación. |

## Uso

```bash
npx -y api-anything@0.3.2 pull sif-chile   # cuando esté publicada en el registry
# o instalar la spec local:
mkdir -p ~/.api-anything/sites
cp integraciones/api-anything/sif-chile.json ~/.api-anything/sites/
cp integraciones/api-anything/sif-chile.md ~/.api-anything/sites/

npx -y api-anything@0.3.2 call sif-chile catalog --fields id,estado,filas --max-chars 2000
npx -y api-anything@0.3.2 call sif-chile schema id=bancos_balance
npx -y api-anything@0.3.2 verify sif-chile --strict
```

La spec es `readOnly: true`, `minTier: 1`: no usa navegador, cookies ni login.
Un id inexistente responde 404 y se clasifica como `input` (corregir el argumento,
no reintentar a ciegas). Las respuestas grandes se recortan y `result` continúa
la vista sin volver al sitio.

## Regenerar y probar

```bash
python3 scripts/build_api_anything.py            # regenera la spec
python3 scripts/build_api_anything.py --check    # CI: falla si está desactualizada
python3 scripts/probar_api_anything.py --check   # prueba real contra espejo local de docs/
python3 scripts/probar_api_anything_etl.py --check  # HTML tier 1 + deriva/reparación (fixtures)
```

La prueba levanta `docs/` con el mismo handler sin caché de la web y apunta la
spec a ese espejo; no depende de que GitHub Pages sea alcanzable desde el runner.
Evidencia: `docs/api/api_anything.log` y `docs/api/api_anything_etl.log`.
