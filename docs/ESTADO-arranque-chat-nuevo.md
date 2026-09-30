# Estado del proyecto y arranque de un chat nuevo

Actualizado 2026-09-30. Este documento sirve para dos cosas: es el resumen del
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
>    dura 2 fotogramas. Ahí sólo se puede afirmar una cota, no un valor.
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

**Resultados vigentes:** `data/processed_data/<video>_v6/`. Las carpetas sin
sufijo y las `_v4` / `_v5` son corridas con la ROI o la base de tiempo mal.
Hay un script `ordenar_carpeta.py` en la raíz que las archiva en
`_superadas/` y deja los documentos en `docs/`.

| documento | para qué |
|---|---|
| `claude/protocolo-analisis-videos.md` | comandos por video y chequeos de aceptación |
| `claude/referencia-archivos-y-graficos.md` | qué contiene cada archivo y cada eje |
| `claude/base-de-tiempo-y-frames-perdidos.md` | el eje temporal. Reemplaza al viejo hallazgo del fps |
| `claude/separacion-estimuladas-espontaneas.md` | enganche de fase y sus límites |
| `claude/comparacion-musclemotion.md` | los números contra MuscleMotion |
| `claude/metricas-cinetica-TTP-RT50.md` | viabilidad de las métricas de cinética |
| `claude/revision-script-matlab.md` | **los errores del script del equipo, para conversarlo con ellos** |
| `claude/cambios-roi-y-k.md` | ROI automática y elección de k |
| `claude/diagnostico-bateria-4videos.md` | el diagnóstico que arrancó todo |

## Resultado de la batería (cerrada)

| video | ROI | var | outliers | k (meseta) | eventos | frecuencia |
|---|---|---|---|---|---|---|
| Video_prueba | 454–1516 | 5.32 % | 3.6 % | 6 (6–15) | 28 | 0.09993 ± 0.000041 Hz |
| Video_063 | 390–1423 | 4.91 % | 7.7 % | 6 (6–8) | 6 | 0.10001 ± 0.000030 Hz |
| Video_268 | 918–1328 | 5.24 % | 2.0 % | 6 (6–20) | 6 | 0.10000 ± 0.000023 Hz |
| Video_466 | 700–900 \* | 5.47 % | 7.9 % | 4 (4–15) | 5 | 0.10006 ± 0.000120 Hz |
| Video_583 | 718–1187 | 5.83 % | 4.0 % | 12 (12–20) | 6 | 0.09999 ± 0.000067 Hz |

Los cinco dan una frecuencia **indistinguible de los 0.1 Hz configurados** y
pasan los tres chequeos de aceptación.

\* Video_466 es el único que necesita ROI forzada (`--x-start 700 --x-end 900`).
El rescate automático elige 944–1169, que es más ancha y cumple planitud
(5.77 %) pero deja 16 % de outliers.

**Video_491 (36 Hz) queda rechazado:** el escaneo no tiene meseta
(12 → 7 → 5 → 4 → 2 → 0, con falsos 16, 7, 2, 2, 1, 0). Se ve algo muy leve en
t ≈ 12.7 y 33.6 s, y MuscleMotion también lo ve, pero ninguno de los dos
métodos puede separarlo del fondo. Descartada la hipótesis de tétanos a 36 Hz:
el alias caería en ~6 Hz y el espectro no tiene nada ahí.

## Qué está pendiente

1. **Implementar TTP, RT50 y amplitud relativa.** Decidido cómo (ver
   `claude/metricas-cinetica-TTP-RT50.md`), falta programarlo. Tres de las
   seis métricas del script del equipo ya las tenemos. El plan acordado es:
   calcular onset/pico/offset sobre la detección ya validada; definir RT50
   como la caída al 50 % del pico (no como lo hace el MATLAB); **marcar la
   métrica como no medible cuando la subida dura menos de ~5 fotogramas**; y
   en ese caso emitir una cota (`TTP < 67 ms`) en vez de un valor.
2. **Conversar con el equipo la adquisición a alta velocidad.** Es la
   limitación de fondo: a 30 fps la cinética de las muestras rápidas no se
   puede medir. Hacen falta 200–300 fps en un subconjunto.
3. **Los videos de `RARITOS`** todavía no se procesaron. Son los que
   MuscleMotion no maneja bien, así que son el caso interesante.
4. **Video de control de iluminación**: mismo gel, quieto, con un cambio de
   luz gradual o un parpadeo. Es lo único que falta para convertir el
   argumento contra MuscleMotion ("medimos geometría de borde, no intensidad")
   en un número.
5. **Si algún video cambia de frecuencia de estimulación a mitad**,
   `rhythm_split` encuentra un solo tren; habría que extenderlo a varios.

## Límites conocidos del método

- Una serie espontánea **muy** regular es indistinguible de una estimulada por
  los tiempos solos. Ahí hay que mirar la amplitud y saber si el estimulador
  estaba encendido.
- `rhythm_split` necesita al menos 4 latidos estimulados.
- El grosor da un salto **positivo** en el fotograma de máxima velocidad: es
  motion blur, no engrosamiento. Usar siempre la medida robusta.
- `04_perfil_frecuencia.png` no resuelve períodos mayores a
  `FREQ_WINDOW_S/2`. Con el default de 8 s no ve el ritmo de 10 s.
- El rescate de ROI por barrido maximiza ancho sujeto a planitud, y puede
  elegir una ventana plana pero con bordes difíciles de seguir (Video_466).
  Mirar siempre el `outlier_frac`.
- **A 30 fps, TTP y RT50 no son medibles cuando la contracción dura menos de
  ~5 fotogramas.** No es un defecto del pipeline: el twitch es más rápido que
  la cámara.
