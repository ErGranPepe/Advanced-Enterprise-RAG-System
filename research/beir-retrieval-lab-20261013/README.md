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
