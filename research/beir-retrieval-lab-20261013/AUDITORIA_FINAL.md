# Auditoría del experimento (13-10-2026)

## Comprobaciones efectuadas
1. Descarga de datasets **BEIR SciFact y NFCorpus** desde la fuente original y coincidencia exacta de MD5: `5f7d1de60b170fc8027bb7898e2efca1` y `a89dba18a62ef92f7d323ec890a0d38d`.
2. Ejecución real en Linux x86_64, Python 3.11, CPU; pesos MiniLM descargados de Hugging Face; no se emplearon preguntas sintéticas para calcular las métricas.
3. Verificación de identidad del código: la versión publicada en `benchmark.py` es idéntica a la ejecutada tras reemplazar solo la ruta fija `/vercel` por `Path(__file__).resolve().parent`. Comparación de archivos: **0 diferencias**.
4. Clonación limpia de esta rama y ejecución de **5 pruebas de regresión**: todas OK. Se incluye test que impide añadir documentos con puntuación léxica cero a la fusión RRF.
5. Resultados medidos guardados en `results/*/summary.json`; casos con mejores y peores diferencias nDCG@10 en `audit_samples.json`.
6. Las dos colecciones emplean el mismo modelo y los mismos hiperparámetros, establecidos antes de inspeccionar qrels, sin ajuste sobre test.

## Procedencia
- Hash SHA-256 del ZIP de SciFact: `536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165`
- Hash SHA-256 del ZIP de NFCorpus: `efe5be03f8c5b86a5870102d0599d227c8c6e2484328e68c6522560385671b0b`
- SHA-256 del script remoto antes del cambio a ruta portátil: `21a6ab1d86bf1ca7c0d2c200ff26c8ba825c0338839b6c02acf372073712bae4`

## Riesgos metodológicos pendientes
- Modelo MiniLM genérico; no se compararon múltiples modelos de embeddings, ni se optimizó su truncamiento.
- Los qrels de ambos benchmarks pueden omitir documentos relevantes.
- No se han probado consultas en español, datos de clientes, documentos confidenciales ni contenido adversarial.
- Sin tests de generación de respuestas, seguridad, costes comerciales ni latencias en entorno real.
- Los intervalos bootstrap son descriptivos: no se corrigieron comparaciones múltiples; no certifican ventaja universal.
- Resultados redondeados a cuatro decimales en los archivos de resumen; el CSV completo por consulta se genera al volver a ejecutar el script, pero **no se versiona** para mantener esta PR ligera.
- Este trabajo demuestra un resultado experimental concreto, no que la búsqueda híbrida sea superior en cualquier colección.

## Revisión editorial
El hallazgo comunicable es doble: RRF tiene una pequeña mejora media en SciFact y NFCorpus, pero **empeora 93 de 623 consultas** en conjunto. En SciFact, TF-IDF por caracteres logró Recall@10 más alto que el híbrido. Se muestran expresamente ambos aspectos, no solo el mejor score.
