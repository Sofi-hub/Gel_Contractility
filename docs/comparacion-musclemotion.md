# Comparación contra MuscleMotion en los cinco videos de `OK`

> **Nota (2026-10-08): los conteos "nuestro" y "meseta" de esta tabla son de septiembre.** Los vigentes están en
> `ESTADO-arranque-chat-nuevo.md`: 063 = 6, 268 = 6, 466 = 5, 583 = 6, y **491 = 2 eventos reportables** desde la
> Fase 2.2 (antes "sin meseta"). Las conclusiones sobre MuscleMotion no cambian. Un argumento nuevo, de los RARITOS
> (`raritos.md`): en Video_476 el brillo da un salto cada 5 fotogramas exactos, también en el fondo vacío
> (probablemente por la compresión del video), y MuscleMotion lo cuenta como ~90 picos; la medida por bordes no lo ve.

Fecha 2026-09-29. La carpeta `OK` contiene los videos donde, en teoría,
MuscleMotion detecta bien, junto con sus salidas. Eso la convierte en el
mejor banco de comparación disponible.

## Los dos métodos, lado a lado

| video | MM picos | avisos de MM | CV interv. MM | nuestro | meseta |
|---|---|---|---|---|---|
| Video_063 | 35 | 19 | 154 % | 6 | k=6–8 |
| Video_268 | 19 | 6 | 94 % | 6 | k=6–20 |
| Video_466 | 6 | 1 | 43 % | 5 | k=4–15 |
| **Video_491** | **47** | **20** | **139 %** | 2 | **sin meseta** |
| Video_583 | 7 | 1 | 4 % | 6 | k=12–20 |

"Avisos de MM" son las líneas `lowUp false at peak` / `lowDown false at peak`
de su propio `Log_file.txt`: picos donde sus chequeos internos de línea de
base fallaron. En Video_063 y Video_491, más de la mitad de sus picos llevan
un aviso.

## Sobre-detección

En Video_063 y Video_268, MuscleMotion encuentra **nuestros eventos y muchos
más**: 5 de nuestros 6 aparecen entre sus picos en los dos videos. La
pregunta es si los extras son contracciones espontáneas reales o ruido.

Se puede acotar. Nuestro método sí detecta espontáneas — en Video_prueba
encuentra 22. En Video_063, bajando el umbral hasta el mínimo del escaneo
(k=3) llegamos a 10 eventos, y de esos, **3 los reproduce el control sobre la
señal invertida**, o sea son ruido. No hay forma de llegar a 35 eventos
reales: MuscleMotion está contando fluctuación.

Lo importante no es que se equivoque más, sino que **no tiene con qué
saberlo**. Su salida no trae un control de falsos positivos, así que sus 35
picos y sus 6 picos se leen igual.

## Video_491: el caso interesante

Es el video donde nosotros no reportamos conteo (sin meseta) y MuscleMotion
reporta **47 picos** con 20 avisos internos y un CV de intervalos del 139 %.
Sus picos están repartidos por los 59 s con un intervalo mediano de 0.9 s.

Los dos eventos que nuestro detector marca (t ≈ 12.7 y 13.2 s) están entre
los de MuscleMotion (12.87 y 13.80 s), así que los dos métodos ven algo ahí.
Pero MuscleMotion ve otras 45 cosas más, con la misma confianza.

Esto sostiene la impresión de que en ese video "se ve algo muy leve": **hay
algo, pero ninguno de los dos métodos puede separarlo del fondo.** La
diferencia es que el nuestro lo dice.

## La escala temporal de MuscleMotion está comprimida

Ver `docs/base-de-tiempo-y-frames-perdidos.md` para el detalle. En resumen:
ImageJ importa menos fotogramas que OpenCV en los cinco videos (déficit de
0.65 % a 4.05 %, según el archivo), y OpenCV coincide exactamente con el
conteo de paquetes de ffprobe. Como MuscleMotion construye su eje temporal
como `fotograma / 30`, ese déficit se traduce en una escala comprimida por un
factor que **depende del archivo**.

Se ve directamente en Video_466: el desfase entre nuestros picos y los suyos
crece linealmente, de 0.57 s en el primer evento a 2.20 s en el quinto. Su
período sale 273.0 fotogramas; predicho a partir del nuestro escalado por el
déficit de fotogramas, 285.25 × 1992/2076 = 273.7.

## Lo que todavía no está medido

Sigue faltando el **video de control de iluminación** (mismo gel, quieto, con
un cambio de luz gradual o un parpadeo). La afirmación "nuestro método es
inmune a cambios sutiles de iluminación porque mide geometría de borde y no
intensidad" sigue siendo teórica. Es lo único barato que falta para cerrar el
argumento.
