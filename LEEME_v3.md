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
