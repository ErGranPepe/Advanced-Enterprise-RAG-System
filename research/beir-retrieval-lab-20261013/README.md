# Retrieval Lab: SciFact y NFCorpus · evaluación reproducible

**Estado:** ejecución empírica real en CPU con dos corpus públicos. La evaluación compara **recuperación de documentos**; no evalúa calidad de respuestas generativas, agentes ni ROI.

## Qué se compara
BM25 (k1=1.2, b=0.75), TF-IDF de palabras (1–2), TF-IDF de caracteres (3–5), `sentence-transformers/all-MiniLM-L6-v2` (vectores normalizados) y fusión RRF de BM25 + MiniLM con k=60. Se utiliza título + texto, 100 candidatos por método, desempate determinista por id y exclusión de coincidencias léxicas con score 0.

**Métrica principal:** nDCG@10. También Recall@10, MRR@10 y Hit@10. Las diferencias respecto a BM25 se evalúan por consulta con 2.000 remuestreos bootstrap pareados (semilla 20261013); no implican causalidad.

## Reproducir
Python 3.11 recomendado y suficiente RAM para inferencia MiniLM en CPU.

```sh
python -m venv .venv
. .venv/bin/activate
pip install "numpy>=1.24,<3" "scipy>=1.10,<2" "scikit-learn>=1.3,<2" "sentence-transformers>=3,<6"
python download.py
python benchmark.py
```

El script guarda `resultados/scifact/{summary.json,per_query.csv}` y lo mismo para NFCorpus.

Datos: BEIR SciFact (5.183 documentos, 300 consultas test) y NFCorpus (323 consultas test). La descarga obtiene los ZIP oficiales y valida los MD5: SciFact `5f7d1de60b170fc8027bb7898e2efca1`; NFCorpus `a89dba18a62ef92f7d323ec890a0d38d`.

## Validación y límites
- No se ajustan modelos ni hiperparámetros mirando las relevancias test.
- Las relevancias (qrels) pueden estar incompletas; documento sin etiqueta no significa necesariamente irrelevante.
- MiniLM usa truncamiento de texto según su configuración interna. No es necesariamente el mejor modelo semántico de cada dominio.
- Las medidas pueden variar con librerías, hardware y tokenización. Esta ejecución usa CPU y lotes de 32 para embeddings.
- **RRF no añade automáticamente valor:** puede perjudicar a consultas individuales. Medimos victorias, derrotas y empates.
- No se debe generalizar a datos corporativos en español ni a soluciones RAG completas.
- No redistribuimos datasets ni pesos en este repositorio; los usuarios los descargan desde sus fuentes.

### Fuentes
- BEIR: https://github.com/beir-cellar/beir
- Datasets BEIR: https://github.com/beir-cellar/beir/wiki/Datasets-available
- MiniLM: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

Esta es una investigación exploratoria independiente. **Los números proceden de ejecución real**, no de resultados sintéticos; incluye salidas por consulta para auditoría.


## Resultados medidos (13 de octubre de 2026)

**Ejecución:** Python 3.11, Linux x86-64, CPU; archivos BEIR oficiales verificados mediante MD5, MiniLM oficial sin ajuste fino; implementación `benchmark.py` basada en los parámetros fijados.

| Método | SciFact nDCG@10 | NFCorpus nDCG@10 |
|---|---:|---:|
| BM25 | 0.6602 | 0.3058 |
| TF-IDF palabras | 0.6209 | 0.2934 |
| TF-IDF caracteres | 0.6639 | 0.3201 |
| MiniLM | 0.6451 | 0.3173 |
| BM25 + MiniLM (RRF) | **0.6841** | **0.3425** |

Diferencia híbrido − BM25 (nDCG@10): SciFact +0.0239, IC bootstrap pareado 95 % [0.0010;0.0457]; NFCorpus +0.0367, IC [0.0217;0.0512]. El híbrido mejora 63 consultas de SciFact, empeora 32 y empata 205; en NFCorpus mejora 126, empeora 61 y empata 136.

**Importante:** el intervalo no prueba superioridad general, y el híbrido **no** obtuvo el Recall@10 más alto en SciFact: TF-IDF de caracteres obtuvo 0.8428 frente a 0.8089 del híbrido. Revisa casos negativos documentados en `results/*/audit_samples.json`.

Ejemplos de retrocesos: consulta SciFact `660` (“Ivermectin is used to treat onchocerciasis.”): BM25 nDCG@10 1.0, híbrido 0.3155; NFCorpus `PLAIN-1320` (“Harvard Physicians’ Study II”): BM25 0.45, híbrido 0.0. Que la media suba no justifica reemplazar el buscador sin revisar regresiones.

Los resultados se generaron en un runner aislado, no contra datos internos de ninguna empresa. `results/*/summary.json` contiene métricas y estadísticas pareadas; `results/*/audit_samples.json` incluye casos con identificación de consulta y documentos. El programa genera además `per_query.csv` al reproducirse, **no está versionado aquí**. No hay benchmark de coste de GPU, producción ni inferencia de LLM generativo.


## Hallazgo específico y herramienta para auditar regresiones

El caso **SciFact #660** está explicado en [results/scifact/CASE_660.md](results/scifact/CASE_660.md): BM25 recupera el documento etiquetado relevante en posición **1**; MiniLM no lo incluye en su top **100** y la fusión RRF lo desplaza a la posición **8**. El informe separa hechos observados de posibles explicaciones.

Para inspeccionar **qué consultas empeoran** después de ejecutar el benchmark:

```bash
python auditar_consultas.py resultados/scifact/per_query.csv --top 15 --threshold 0.1 --out regresiones_scifact.json
python auditar_consultas.py resultados/nfcorpus/per_query.csv --top 15 --threshold 0.1 --out regresiones_nfcorpus.json
```

El script únicamente necesita Python estándar. Está probado con datos de control; la auditoría usa pares de resultados de la **misma consulta**. No sustituye la revisión manual de casos prioritarios.
