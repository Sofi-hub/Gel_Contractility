# Estado del proyecto y arranque de un chat nuevo

Actualizado 2026-09-30 (tarde). Este documento sirve para dos cosas: es el resumen del
estado actual, y su primera sección se puede pegar tal cual al abrir un chat
nuevo dentro del proyecto.

---

## Prompt para pegar en el chat nuevo

> Trabajo en `gel_contractility`, un pipeline en Python que mide
> contractilidad de geles 3D a partir de video de microscopía. Funciona y está
> validado sobre seis videos; el código y los documentos están en este
> proyecto.
>
> **Cómo funciona, en una línea por etapa:** el video se convierte en un mapa
> de máxima intensidad, de ahí se detecta automáticamente la *gauge region*
> (la zona plana del gel, lejos de los anclajes), en cada fotograma se
> localizan los dos bordes del gel con precisión subpíxel en ~60 columnas, se
> ajusta un polinomio de grado 2 con RANSAC de umbral adaptativo para
> descartar columnas arruinadas por burbujas, y de ahí salen cuatro series
> temporales: `y_top_px`, `y_bottom_px`, `thickness_px` (la resta) y
> `center_px` (el promedio). Después se detectan los eventos de contracción y
> se los separa en estimulados y espontáneos por enganche de fase.
>
> **Los cinco hallazgos que definen el método, y que no hay que perder:**
>
> 1. **La contracción se detecta sobre `center_px`, no sobre
>    `thickness_px`.** En este montaje la contracción es mayormente un
>    desplazamiento vertical de toda la franja, y el grosor, al ser la resta
>    de los dos bordes, es ciego a la traslación. Medido: SNR por fotograma 44
>    en `center_px` contra 3 en `thickness_px`. **Cuánto del movimiento es
>    adelgazamiento depende del video** (18 % y 13 % en los dos de referencia,
>    1–2 % y no significativo en Video_268 y Video_583): no es una constante
>    del montaje.
> 2. **Los estimulados se separan de los espontáneos por enganche de fase**,
>    no por amplitud ni por ventana temporal. El estimulador dispara en
>    `t = fase + n·T`; se busca esa grilla y lo que queda afuera es
>    espontáneo. Como la amplitud no se usa para clasificar, sirve de
>    verificación independiente.
> 3. **El eje temporal sale de los timestamps del contenedor, no de
>    `fotograma / fps`.** El fps declarado es un promedio y baja cuando la
>    grabación pierde fotogramas, con lo cual los eventos parecen más juntos
>    de lo que fueron. Correr siempre con `--base-tiempo pts`. El fps real de
>    captura es 30.000 (el `dt` mediano de los timestamps da 33.333 ms en los
>    cinco videos).
> 4. **El umbral `k` se elige dentro de la meseta del escaneo de
>    estabilidad**, y ya es automático (`--k auto`, el default). Si no hay
>    meseta con 0 falsos de control, el conteo **no se reporta**.
> 5. **A 30 fps la cinética de contracción (TTP, RT50) no es medible en las
>    muestras rápidas.** En tres de los cinco videos la contracción entera
>    dura 2 fotogramas. Ahí sólo se puede afirmar una cota (TTP < 100 ms),
>    no un valor. Ya está implementado (`src/cinetica.py`): da el valor solo
>    si la subida ocupa ≥ 5 fotogramas y, si no, la cota.
>
> **Fuera de alcance por decisión del proyecto:** no se calibra píxeles a
> milímetros. Los videos no se graban todos al mismo aumento, así que un
> factor único no tendría sentido. `px_to_mm` queda en 1.0 y todo se reporta
> en píxeles; las comparaciones entre videos son relativas (porcentaje,
> cocientes) o dentro de un mismo aumento.
>
> **Principio de trabajo:** el código original estaba sobreajustado a un solo
> video y eso causó varios problemas. Antes de dar por bueno cualquier
> resultado hay que verificarlo: meseta del escaneo de umbral, control de
> falsos positivos sobre la señal invertida, y regresión sobre los dos videos
> validados cuando se toca un algoritmo. Nada de tunear un parámetro hasta que
> el número dé lindo.
>
> Leé `claude/protocolo-analisis-videos.md` y
> `claude/referencia-archivos-y-graficos.md` antes de interpretar salidas.

---

## Dónde está todo

**Resultados vigentes:** `data/processed_data/<video>/`, **sin sufijo**. Se
generaron como `<video>_v6`; `ordenar_carpeta.py` archivó todo lo anterior
(las primeras corridas, `_v4` y `_v5`, con la ROI o la base de tiempo mal) en
`data/processed_data/_superadas/` y les quitó el sufijo a los vigentes. Ese
script ya se aplicó y ahora se niega a correr de nuevo (si no, archivaría los
vigentes).

**Cuidado:** en `.claude/worktrees/video-processing-pipeline-10178f/` hay una
copia vieja del código, anterior a la v4. No es el código vigente.

| documento | para qué |
|---|---|
| `claude/protocolo-analisis-videos.md` | comandos por video y chequeos de aceptación |
| `claude/referencia-archivos-y-graficos.md` | qué contiene cada archivo y cada eje |
| `claude/base-de-tiempo-y-frames-perdidos.md` | el eje temporal. Reemplaza al viejo hallazgo del fps |
| `claude/separacion-estimuladas-espontaneas.md` | enganche de fase y sus límites |
| `claude/comparacion-musclemotion.md` | los números contra MuscleMotion |
| `claude/contexto-tecnun-y-musclemotion.md` | para quién es el trabajo y qué es la carpeta `OK` de MuscleMotion |
| `claude/metricas-cinetica-TTP-RT50.md` | cinética: viabilidad, implementación y resultados |
| `claude/guia-revision-codigo.md` | **guía para revisar todo el código en un chat aparte** |
| `DOCUMENTACION.md` | el método sin código, para quien diseña el experimento |
| `claude/revision-script-matlab.md` | **los errores del script del equipo, para conversarlo con ellos** |
| `claude/cambios-roi-y-k.md` | ROI automática y elección de k |
| `claude/diagnostico-bateria-4videos.md` | el diagnóstico que arrancó todo |

## Resultado de la batería (cerrada)

| video | ROI | var | outliers | k (meseta) | eventos | frecuencia |
|---|---|---|---|---|---|---|
| Video_prueba | 454–1516 | 5.32 % | 3.6 % | 6 (6–15) | 28 → **29** (Fase 2.2) | 0.09993 ± 0.000041 Hz |
| Video_063 | 390–1423 | 4.91 % | 7.7 % | 6 (6–8) | 6 | 0.10001 ± 0.000030 Hz |
| Video_268 | 918–1328 | 5.24 % | 2.0 % | 6 (6–20) | 6 | 0.10000 ± 0.000023 Hz |
| Video_466 | 700–900 \* | 5.47 % | 7.9 % | 4 (4–15) | 5 | 0.10006 ± 0.000120 Hz |
| Video_583 | 718–1187 | 5.83 % | 4.0 % | 12 (12–20) | 6 | 0.09999 ± 0.000067 Hz |

Los cinco dan una frecuencia **indistinguible de los 0.1 Hz configurados** y
pasan los tres chequeos de aceptación.

Cinética (2026-09-29, detalle en `claude/metricas-cinetica-TTP-RT50.md`):

| video | TTP | RT50 | amplitud relativa |
|---|---|---|---|
| Video_prueba, Video_063, Video_268 | no medible: < ~100 ms | no medible: < ~100 ms | 0.71 / 0.53 / 0.57 % |
| Video_466 | 284 ms [137, 365] | 160 ms [70, 260] | 2.13 % |
| Video_583 | 258 ms [129, 335] | 181 ms [99, 301] | 1.31 % |
| Video_491 (desde la Fase 2.2) | 570 ms | 467 ms | 0.40 % |

\* Video_466 es el único que necesita ROI forzada (`--x-start 700 --x-end 900`).
El rescate automático elige 944–1169, que es más ancha y cumple planitud
(5.77 %) pero deja 16 % de outliers.

**Video_491 (36 Hz): desde la Fase 2.2 (2026-10-01) da 2 eventos reportables**
(13.0 y 34.0 s). Antes salía "sin meseta" porque la mediana móvil de 2 s se comía
sus eventos, que duran ~1 s (el doble que los de los otros videos). Con la
ventana automática (3.1 s) el conteo es 2 con 2.3, 3.1 y 4.7 s. Pero es distinto
de los otros cinco en dos cosas: la duración y el **sentido** (la franja sube en
la pantalla; en los demás baja). Consultar con el equipo cómo se estimuló antes
de citarlo. Una contracción sostenida de ~1 s a 36 Hz es compatible con un
tétanos fusionado; el descarte anterior del tétanos buscaba una ondulación a
~6 Hz que un tétanos fusionado no tiene.

## Qué está pendiente

**Hecho el 2026-09-29/30:** TTP, RT50 y amplitud relativa (`src/cinetica.py`);
corrección de inconsistencias en la documentación (`_v6`, `DOCUMENTACION.md`
reescrita, `--base-tiempo pts` como default de `main.py`,
`analyze_contractions.py` marcado obsoleto, escaneos vigentes agregados a
`tests/test_seleccion_k.py`); guía de revisión (`claude/guia-revision-codigo.md`).

**Hay una revisión de código en curso en otro chat.** Sus hallazgos van a
`claude/hallazgos-revision-codigo.md`. Leerlo antes de tocar un módulo.

0. **✅ RESUELTO 2026-10-01** (`src/estadistica.py`, `tests/test_nan.py`; ver
   "Implementación" en `claude/hallazgos-revision-codigo.md`). **Era: un solo
   fotograma `REJECTED` anulaba el reporte en silencio.** `contraction_report.mad()` no ignora `NaN`: con un
   solo fotograma rechazado el ruido da `NaN` y el reporte dice "no hay
   meseta" con 0 eventos. Hoy no afecta a ningún resultado (los seis vigentes
   no tienen fotogramas rechazados). Detalle: H1 en
   `claude/guia-revision-codigo.md`.
0b. **✅ 2026-10-01: un solo detector.** `src/event_detection.py` y
   `scripts/analyze_contractions.py` se borraron (no aportaban nada que no
   estuviera en el reporte); la figura del escaneo de `k` (`05_*`) ahora la
   genera `contraction_report.py` con su propio escaneo.
0c. **✅ 2026-10-01: Fase 2.2 aplicada.** Un evento se define por altura y
   prominencia (sin `sep_s`); ventana del detrend automática con control de
   estabilidad; grilla fina de `k` con el `k` en el centro de la meseta y todas
   las mesetas listadas. **Nueva línea base: Video_prueba = 29 eventos;
   Video_491 = 2, reportable.** Los otros cuatro, iguales. Ver
   `claude/propuesta-fase-2-2.md` y `tests/test_deteccion.py`.
1. **Conversar con el equipo la adquisición a alta velocidad.** Es la
   limitación de fondo: a 30 fps la cinética de las muestras rápidas no se
   puede medir. Hacen falta 200–300 fps en un subconjunto.
2. **Los videos de `RARITOS`** todavía no se procesaron. Son los que
   MuscleMotion no maneja bien, así que son el caso interesante.
3. **Video de control de iluminación**: mismo gel, quieto, con un cambio de
   luz gradual o un parpadeo. Es lo único que falta para convertir el
   argumento contra MuscleMotion ("medimos geometría de borde, no intensidad")
   en un número.
4. **Si algún video cambia de frecuencia de estimulación a mitad**,
   `rhythm_split` encuentra un solo tren; habría que extenderlo a varios.

Mejoras propuestas (no están en ningún pedido; ordenadas por valor/esfuerzo):

5. **Test de regresión automático** contra los `contracciones.xlsx` vigentes
   (hoy la regla "Video_prueba y Video_063 no cambian" se chequea a mano).
6. **Script por lotes** con una tabla consolidada, una fila por video. Útil
   para `RARITOS`.
7. **Que la ROI automática mire también `outlier_frac`**: Video_466 es el
   único que necesita ROI forzada.
8. **Adelgazamiento relativo** (`adelgazamiento_robusto_px / grosor en
   reposo`): deformación sin calibrar.
9. **Cinética por grupo** (estimulados vs espontáneos).
10. **Intervalos de confianza por bootstrap** para las medianas por video.
11. **Versiones fijas en `requirements.txt`.**

## Límites conocidos del método

- Una serie espontánea **muy** regular es indistinguible de una estimulada por
  los tiempos solos. Ahí hay que mirar la amplitud y saber si el estimulador
  estaba encendido.
- `rhythm_split` necesita al menos 4 latidos estimulados.
- El grosor da un salto **positivo** en el fotograma de máxima velocidad: es
  motion blur, no engrosamiento. Usar siempre la medida robusta.
- El rescate de ROI por barrido maximiza ancho sujeto a planitud, y puede
  elegir una ventana plana pero con bordes difíciles de seguir (Video_466).
  Mirar siempre el `outlier_frac`.
- **A 30 fps, TTP y RT50 no son medibles cuando la subida dura menos de ~5
  fotogramas.** No es un defecto del pipeline: el twitch es más rápido que la
  cámara. En esos casos se reporta la cota (TTP < 100 ms), no un valor.
- En las muestras lentas (466, 583) **el pico es una meseta** de 4–5
  fotogramas: el instante del pico es ambiguo y los intervalos de TTP/RT50
  son anchos. El inicio de la contracción sí está bien definido.
