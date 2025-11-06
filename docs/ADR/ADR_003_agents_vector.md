# ADR-003: Agentes — adoptar Vector

## Contexto
Se buscan agentes de ingesta de alto rendimiento, baja huella y transformaciones tempranas.

## Decisión
Usar Vector como agente predeterminado para nuevas fuentes; coexistencia breve con Fluentd si existe.

## Alternativas
- Fluent Bit: ligero y estable; Vector ofrece VRL más potente.
- Fluentd: más pesado; adecuado si ya está desplegado.

## Consecuencias
- Mejor throughput y costos operativos.
- Transformaciones tempranas con VRL para enriquecer tenant/dataset.