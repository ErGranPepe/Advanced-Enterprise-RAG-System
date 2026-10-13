# Análisis de regresión: SciFact, consulta 660

**Consulta original:** `Ivermectin is used to treat onchocerciasis.`

En SciFact, las etiquetas públicas de test marcan un único documento como relevante: `1215116` (*“Rapid-Impact Interventions”: How a Policy of Integrated Control for Africa's Neglected Tropical Diseases Could Benefit the Poor*).

## Hallazgo reproducido con el script del benchmark

| Recuperador | Posición del documento 1215116 |
|---|---:|
| BM25 | **1** |
| MiniLM (`all-MiniLM-L6-v2`) | **Fuera del top 100** |
| BM25 + MiniLM (RRF, k=60) | **8** |

Para esta consulta con un único relevante en las etiquetas, el nDCG@10 pasa de `1,0000` (BM25) a `0,3155` (RRF).

- La puntuación BM25 del documento fue **8,9296**, la mayor entre los 5.183 textos.
- La similitud coseno del mismo documento con MiniLM fue **0,1982** en la ejecución analizada.
- El primer resultado de MiniLM fue el documento `3308636` (*Interferons: Success in anti-viral immunotherapy.*), **no etiquetado como relevante** para la consulta.
- RRF fusiona posiciones, no interpreta la puntuación BM25 absoluta como una certeza. Documentos que aparecen en posiciones suficientemente favorables de ambas listas pueden desplazar el primero de una lista cuando la otra no lo incluye.

## Interpretación responsable

Este ejemplo demuestra una **regresión individual causada por el cambio de ranking al fusionar**. Es consistente con dificultades de recuperación semántica para terminología especializada, pero **un único caso no demuestra** que MiniLM falle sistemáticamente con términos biomédicos raros, ni que BM25 sea superior globalmente.

Tampoco demuestra que el artículo etiquetado como relevante sea la única fuente científicamente correcta. Las evaluaciones de relevancia son etiquetas del benchmark, no un dictamen clínico ni una auditoría exhaustiva de toda la colección.

## Regla práctica

Antes de desplegar un buscador híbrido:

1. Calcula nDCG/Recall sobre un conjunto representativo de consultas y etiquetas independientes.
2. Ordena las consultas por **caída de calidad respecto al baseline**; identifica las que sean prioritarias o sensibles.
3. Inspecciona las contribuciones de cada recuperador y prueba ablaciones (sin fusión, pesos diferentes, exclusión de puntuaciones cero).
4. Establece umbrales de regresión por segmentos críticos antes de decidir si activar el híbrido.

El script `auditar_consultas.py` permite examinar las regresiones a partir del CSV generado por `benchmark.py`.

**Evidencia:** BEIR SciFact qrels/test.tsv, ejecución original del benchmark sobre 300 consultas SciFact, reproducción de esta consulta con ambos recuperadores, 13 octubre 2026.

## Por qué RRF produjo exactamente ese cambio

Los **siete documentos** situados antes que el documento relevante en el ranking híbrido aparecían dentro del top 100 de **ambos** recuperadores. En cambio, el relevante solo aparecía en el top 100 de BM25.

El **primer documento del híbrido** (`5402581`, sin etiqueta de relevancia para q660) estaba en el puesto **12** de BM25 y **20** de MiniLM. RRF con `k=60` suma:

`RRF(5402581) = 1/(60+12) + 1/(60+20) = 0.026389`

El documento etiquetado como relevante (`1215116`) estaba **primero** en BM25, pero **fuera del top 100** de MiniLM, por lo que solo obtiene:

`RRF(1215116) = 1/(60+1) = 0.016393`

**Resultado:** un documento en los puestos 12 y 20 de dos rankings supera al puesto 1 de uno solo. No es un fallo de implementación: es el comportamiento de esta configuración de fusión de rankings. Se debe valorar con las etiquetas de relevancia y el contexto de uso.
