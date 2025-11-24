#!/usr/bin/env python3
"""
Setup / ensure ingest pipeline 'logs_ingest' in OpenSearch.

Hace:
- GET pipeline si existe -> muestra definición.
- Si no existe o se pasa --force, crea/actualiza pipeline básica.
- Opcionalmente valida con un documento de prueba (--test).

Uso:
  python scripts/setup_ingest_pipeline.py
  python scripts/setup_ingest_pipeline.py --force
  python scripts/setup_ingest_pipeline.py --test '{"message":"hello","tenant_id":"acme"}'

Vars:
  OPENSEARCH_HOST (default: localhost:9201 si ejecutas fuera de contenedor; dentro usar opensearch:9200)
"""
import argparse
import json
import os
import sys
from urllib import error, request


def os_url() -> str:
    host = os.getenv("OPENSEARCH_HOST", "localhost:9201")
    if host.startswith("http://") or host.startswith("https://"):
        return host
    return f"http://{host}"


def get_pipeline(url: str, name: str):
    req = request.Request(f"{url}/_ingest/pipeline/{name}", method="GET")
    try:
        with request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"[WARN] GET pipeline error {e.code}")
    except Exception as e:
        print(f"[WARN] GET pipeline exception: {e}")
    return None


def put_pipeline(url: str, name: str, definition: dict):
    data = json.dumps(definition).encode("utf-8")
    req = request.Request(
        f"{url}/_ingest/pipeline/{name}",
        method="PUT",
        headers={"Content-Type": "application/json"},
        data=data,
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                print(f"[OK] Pipeline '{name}' creada/actualizada.")
            else:
                print(f"[WARN] PUT pipeline status {resp.status}")
    except Exception as e:
        print(f"[ERROR] PUT pipeline failed: {e}")
        sys.exit(1)


def simulate(url: str, name: str, doc: dict):
    payload = {"pipeline": name, "docs": [{"_source": doc}]}
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{url}/_ingest/pipeline/_simulate",
        method="POST",
        headers={"Content-Type": "application/json"},
        data=data,
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            print("[SIMULATE] Response:")
            print(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[WARN] simulate failed: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Forzar recreación del pipeline")
    parser.add_argument("--test", type=str, help="Documento de prueba en JSON para simular")
    args = parser.parse_args()

    url = os_url()
    name = "logs_ingest"

    existing = get_pipeline(url, name)
    if existing and not args.force:
        print(f"[INFO] Pipeline '{name}' ya existe. Usa --force para recrear.")
    else:
        definition = {
            "description": "Pipeline de ingestión básica Nubla (normalización ligera futura).",
            "processors": [
                # Ejemplo: añadir etiqueta si falta severity
                {"script": {"if": "ctx.severity == null", "source": "ctx.severity='info'"}},
                # Capitalizar host (ejemplo simple)
                {"script": {"if": "ctx.host != null", "source": "ctx.host = ctx.host.toString()"}},
            ],
        }
        put_pipeline(url, name, definition)

    # Mostrar pipeline final
    final = get_pipeline(url, name)
    if final:
        print(json.dumps(final, indent=2))
    else:
        print("[ERROR] No se pudo recuperar pipeline tras creación.")

    if args.test:
        try:
            doc = json.loads(args.test)
        except Exception:
            print("[ERROR] JSON inválido en --test")
            sys.exit(1)
        simulate(url, name, doc)


if __name__ == "__main__":
    main()
