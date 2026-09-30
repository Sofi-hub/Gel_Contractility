# Ronda 3 — la contraccion SI esta en Video_063; el observable estaba mal

## Resultado

Video_063 tiene 5 contracciones limpias, con marcapaso perfectamente regular
cada **10.044 s (0.0996 Hz)**. Video_prueba tiene el mismo marcapaso:
**10.091 s (0.0991 Hz)**. Los dos videos estan estimulados igual. Video_063
nunca estuvo roto: contrae ~4.4 veces mas debil.

Lo que fallaba era el OBSERVABLE. La contraccion no se manifiesta
principalmente como adelgazamiento sino como un desplazamiento vertical de
toda la franja: los dos bordes se mueven juntos, y el grosor (que es la
resta de los dos) es ciego a esa parte del movimiento.

|                                  | Video_prueba | Video_063 |
|----------------------------------|--------------|-----------|
| traslacion por evento (center_px)| 6.64 px      | 1.51 px   |
| adelgazamiento (medida robusta)  | 0.77 px      | 0.19 px   |
| cociente adelgazamiento/traslacion | 15.4 %     | 12.8 %    |
| ruido por frame de center_px     | 0.086 px     | 0.034 px  |
| ruido por frame del grosor       | 0.089 px     | 0.065 px  |

El cociente es del mismo orden en los dos videos: **la mecanica de la
contraccion es la misma**, cambia la amplitud. El grosor es un observable
atenuado ~6x respecto de la traslacion, asi que necesita ~6x mas senal para
llegar al mismo SNR. En Video_prueba la traslacion es lo bastante grande
como para que el resto igual asome sobre el ruido; en Video_063 no.

## Prueba de estabilidad del umbral (falsos = mismo detector sobre la senal invertida)

Video_063:

    center_px       k=6..8   -> 6 eventos, 0 falsos
                    k=10..20 -> 5 eventos, 0 falsos     <- meseta limpia
    thickness_px    k=3      -> 7 eventos, 11 falsos    <- ruido
                    k=4      -> 7 eventos, 5 falsos
                    k>=6     -> 0 eventos

Esa segunda tabla es exactamente el sintoma original: con `--amp-k 3.0`
aparecian eventos mezclados con falsos positivos, y con `--amp-k 6.0`
no aparecia ninguno. No era un problema de umbral ni de sobreajuste del
detector: era que se estaba midiendo la variable equivocada.

Video_prueba, para comparar: `center_px` da meseta de 10 eventos desde k=6
hasta k=20 con 0 falsos.

## Sobre la hipotesis del anclaje flojo

**No hace falta.** Video_prueba, que funciona, muestra el MISMO modo
dominado por traslacion y con un cociente adelgazamiento/traslacion
parecido. Si un extremo suelto explicara Video_063, el video de control
deberia mostrar adelgazamiento puro, y no lo hace. Es la mecanica normal
de este montaje, no un defecto de la muestra 063.

## Script nuevo: scripts/contraction_report.py

    python scripts/contraction_report.py --input .../serie_temporal.xlsx
    python scripts/contraction_report.py --input A.xlsx --compare B.xlsx

Hace tres cosas:

1. **Detecta sobre `center_px`** (posicion media de la franja), no sobre
   el grosor. Decide solo el signo de los eventos mirando que cola de la
   distribucion es mas pesada, asi que no depende de la convencion de la
   imagen ni de si el gel sube o baja al contraerse.
2. **Escaneo de estabilidad con control simetrico**: corre el mismo
   detector sobre la senal invertida. Una contraccion solo puede ir en un
   sentido, asi que todo lo que aparece del lado invertido es ruido.
3. **Mide el adelgazamiento promediando los eventos alineados**
   (event-locked average). Con 5 eventos el ruido del promedio baja
   sqrt(5) y el adelgazamiento de Video_063 pasa de ~1 sigma por frame a
   11 sigma. El grosor sigue siendo la variable biomecanicamente
   interesante; lo que no sirve es usarlo para DETECTAR.

### Artefacto de motion blur (detectado y avisado por el script)

En el frame de maxima velocidad el grosor medido da un salto POSITIVO
(+0.39 px en 063, +0.17 px en prueba). No es engrosamiento: el borde se
emborrona por el movimiento y los dos bordes se "abren". Por eso el script
reporta dos medidas y avisa:

- `minimo`: el minimo del promedio alineado (puede estar contaminado)
- `robusto`: promedio de los 3 frames POSTERIORES al pico (evita el blur)

Usar siempre la robusta para comparar entre videos.

## Que sigue

- Falta el test de CLAHE on/off. Es la prueba de si estamos reintroduciendo
  sensibilidad a iluminacion por la puerta de atras.
- `--px-to-mm` sigue en 1.0: todos los "mm" de las salidas son px.
- Para el argumento contra MuscleMotion conviene un video de control donde
  SOLO cambie la luz y el gel no se mueva.

---

# Parche v3.1 — `--sep-s` estaba borrando eventos reales

Síntoma: en Video_prueba, el tren de contracciones espontáneas del principio
se graficaba bien pero solo 4-5 picos quedaban marcados como eventos.

Causa: `find_peaks(distance=...)` se queda con el pico **más alto** de cada
ventana de ese ancho. El default era `--sep-s 2.0` y el tren espontáneo va a
1.75 Hz (un evento cada 0.57 s), así que de cada 2 segundos sobrevivía uno.
No era ruido ni umbral: era el detector descartando por proximidad.

    --sep-s 2.00  ->  10 eventos ( 5 espontaneos + 5 estimulados)
    --sep-s 1.00  ->  16 eventos (10 + 6)
    --sep-s 0.50  ->  26 eventos (20 + 6)
    --sep-s 0.30  ->  29 eventos (23 + 6)   <- nuevo default
    --sep-s 0.15  ->  29 eventos (23 + 6)   estable

Con 0 falsos de control en todos los casos: los 23 son reales.

Cambios:

1. **Default de `--sep-s` bajado de 2.0 a 0.3 s.**
2. **Aviso automático**: si bajando la separación aparecerían bastantes más
   picos, el script lo dice y sugiere bajar `--sep-s`.
3. **Detección de dos poblaciones**: si las amplitudes se separan en dos
   grupos (razón de medianas ≥ 2), se reportan por separado, porque
   promediarlas juntas da una amplitud y una frecuencia que no describen a
   ninguna. Sobre Video_prueba:

        grupo       n    amplitud_px    intervalo_s      Hz    ventana_s
        chicos     23          2.068          0.572    1.75    0.4 - 16.2
        grandes     6          6.807         10.091    0.10   14.8 - 65.3

   Se guarda en la hoja `poblac_<video>` de `contracciones.xlsx`.

---

# v3.2 — separacion de estimuladas vs espontaneas (`src/rhythm_split.py`)

    python scripts/contraction_report.py --input .../serie_temporal.xlsx --frecuencia-estimulo 0.1

## El criterio

No es la amplitud (con estimulacion debil se solapan) ni la ventana temporal
(las espontaneas siguen apareciendo durante el tren). Es el **enganche de
fase**: el estimulador dispara en t = fase + n*T, y las espontaneas no saben
nada de ese reloj. Se busca la grilla (T, fase) que mejor explica un
subconjunto de los eventos; lo que queda afuera es espontaneo.

La amplitud NO se usa para clasificar, y por eso sirve de verificacion
independiente: si los grupos salen con amplitudes distintas sin que la
amplitud haya intervenido, la separacion es real.

## Resultados sobre los dos videos

| | Video_prueba | Video_063 |
|---|---|---|
| estimulados | 6 (100 % de captura) | 4 + 1 dudoso |
| espontaneos | 22 | 1 |
| **periodo** | **10.09118 +- 0.00232 s** | **10.04356 +- 0.00432 s** |
| **frecuencia** | **0.09910 +- 0.000023 Hz** | **0.09957 +- 0.000043 Hz** |
| jitter | < 1 fotograma | < 1 fotograma |
| z / p | 17.3 / 0.005 | 17.3 / 0.005 |
| amplitud estimulados | 6.81 px | 1.57 px |
| amplitud espontaneos | 2.06 px | — |

Las espontaneas de Video_prueba: intervalo mediano 0.572 s (1.75 Hz) con
**CV 91 %**. No se reporta como "una frecuencia": estas celulas no la
mantienen constante, asi que sale la mediana, el rango intercuartil y la
frecuencia **instantanea** evento a evento (hoja `espont_*`).

## Hallazgo: el fps de los videos esta mal

La frecuencia medida da 0.0991 y 0.0996 Hz contra 0.1000 configurado: un
sesgo del -0.9 % y del -0.43 %, del mismo signo y muy significativo
(t = -39 y t = -10). El estimulador es un reloj de cuarzo; el `fps` del
archivo no. Y en los dos videos:

    fotogramas por periodo = 300.0 exactos   ->   fps real = 30.000

contra 29.7289 y 29.8699 declarados. Dos videos independientes, con fps
declarados distintos, dan el mismo fps corregido. **Es el fps, no el equipo.**

Consecuencia: todos los tiempos y frecuencias del analisis estan escalados
entre 0.4 % y 0.9 %. Para magnitudes absolutas conviene reprocesar con
fps = 30, o al menos registrarlo.

## Tres cosas que hubo que resolver (estan documentadas en el codigo)

1. **Armonicos.** El z-score solo hacia que ganara T/3 = 3.362 s con 44 % de
   captura. Se exige `min_captura` (75 %) y, entre los candidatos que puntuan
   casi igual, se elige el periodo MAS LARGO: un armonico siempre esta en
   T/2, T/3, ... o sea siempre es menor.
2. **Intrusos con brazo de palanca.** Un espontaneo tomado como primera
   ranura movia el periodo de 10.091 a 10.127 s y repartia su error entre
   todos los residuos, con lo cual ninguna limpieza lo sacaba. Se ajusta
   primero con **Theil-Sen** (mediana de pendientes de a pares) y recien al
   final por minimos cuadrados sobre el conjunto limpio.
3. **Error estandar cero.** El tren cae siempre en el mismo numero de
   fotogramas, asi que los residuos daban exactamente 0. Se pone como piso la
   cuantizacion, resolucion/sqrt(12).

## Latidos dudosos

Un latido del tren cuyo instante detectado se corrio mas que la tolerancia
no se tira ni se mezcla con las espontaneas: se reporta como
`estimulados_dudosos`. En Video_063 el 5o latido aparece 335 ms antes de su
ranura, y su amplitud (1.51 px) coincide con la de los estimulados
(1.57 px), no con nada mas. Es un latido del tren, no una espontanea.

## Salidas nuevas

`10_ritmo.png` (eventos coloreados por grupo, grilla del estimulador, y el
error de cada latido en ms) y las hojas `ritmo_*`, `grilla_*` y `espont_*`
de `contracciones.xlsx`.
