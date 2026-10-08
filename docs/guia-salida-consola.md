# Guía de la salida de consola (para analizar videos en vivo)

Actualizada el 2026-10-07, después de limpiar la consola (commit `4e4d37e`). Explica **todo lo que puede aparecer en pantalla** al analizar un video, qué es normal, cuándo preocuparse y qué contestar si alguien pregunta. Los ejemplos son salidas reales de Video_476 (caso limpio), Video_613 (no reportable por vibración) y Video_068 (actividad continua).

**Regla general:** lo que no aparece en pantalla igual queda guardado en los Excel (`serie_temporal_<video>.xlsx`, `contracciones_<video>.xlsx`, `movimiento_<video>.xlsx`). Para ver todo el detalle técnico también en pantalla, agregá `--verbose` al final de cualquier comando: esas líneas extra empiezan con `[detalle]`.

---

## 0. La forma fácil: la ventana

Doble clic en **`Analizar.bat`** (en la carpeta del proyecto). Se abre una ventana:
1. **Video:** botón "Elegir..." o arrastrar el archivo a la ventana. Para arrastrar hay que instalar una vez `pip install tkinterdnd2` con el entorno activado.
2. **Guardar resultados en:** se completa sola con `data\processed_data\<nombre del video>`; se puede cambiar. El nombre de esa carpeta es el que aparece en los títulos de los gráficos y de las hojas del Excel.
3. **Qué correr:** los tres pasos de la sección 1, por separado o juntos. Los pasos 2 y 3 usan el `serie_temporal_<video>.xlsx` que ya esté en la carpeta, así que se pueden repetir (por ejemplo, con otra frecuencia) sin volver a medir el gel.
4. **Opciones:** frecuencia del estimulador, "el gel se mueve mucho" (`--half-window 30`) y detalle técnico (`--verbose`).
5. **Analizar.** Abajo aparece en vivo lo mismo que en la consola: los avisos en rojo y los títulos en azul. "Detener" corta el paso en curso y "Abrir carpeta de resultados" abre la carpeta en el explorador de archivos.

La ventana no calcula nada propio: corre los mismos comandos de la sección 1, así que los números son idénticos. Si un paso falla, muestra el error y no corre los siguientes.

## 1. Comandos (copiar y pegar)

Abrir PowerShell en la carpeta del proyecto y activar el entorno:

```
cd "C:\Users\Franco Rita\Facultad\Espana\Análisis_de_Datos\gel_contractility_git\Gel_Contractility"
.venv\Scripts\Activate.ps1
```

Para cada video, **cambiar solo la primera línea** (el nombre del archivo, sin `.mp4`). Se supone que el video está en `data\raw_videos\`, al lado de `Video_prueba.mp4`.

```
$v = "Video_XXX"
```

**Paso 1: medir el gel en cada fotograma** (tarda unos minutos):

```
python main.py --video "data\raw_videos\$v.mp4" --output-dir "data\processed_data\$v" --base-tiempo pts
```

**Paso 2: buscar las contracciones.** Si saben a qué frecuencia estaba el estimulador (por ejemplo 0.1 Hz):

```
python scripts\contraction_report.py --input "data\processed_data\$v\serie_temporal_$v.xlsx" --frecuencia-estimulo 0.1
```

Si no lo saben, el mismo comando sin `--frecuencia-estimulo 0.1`. Si hubo dos frecuencias en el mismo video: `--frecuencia-estimulo 0.1 0.2`.

**Paso 3 (opcional): confirmar el movimiento por otro método.** Mide la imagen entera sin usar los bordes y tarda unos minutos más:

```
python scripts\motion_check.py --video "data\raw_videos\$v.mp4" --serie "data\processed_data\$v\serie_temporal_$v.xlsx"
```

**Si el paso 1 avisa que hay muchos fotogramas sin borde** (ver 2.4), repetir el paso 1 en otra carpeta con la ventana más grande y seguir desde ahí:

```
python main.py --video "data\raw_videos\$v.mp4" --output-dir "data\processed_data\${v}_hw30" --base-tiempo pts --half-window 30
python scripts\contraction_report.py --input "data\processed_data\${v}_hw30\serie_temporal_$v.xlsx"
```

Todos los resultados quedan en `data\processed_data\<video>\`.

---

## 2. Paso 1: `main.py`

### Ejemplo limpio (Video_476)

```
Procesando data\raw_videos\Video_476_EXP5_FAPS5_40V.mp4 ...
Zona analizada del gel: columnas 981 a 1249 (268 px de ancho)
  variacion del grosor dentro de la zona: 2.64% (aceptable hasta 6%) -> OK
  nota: la camara perdio ~42 fotogramas (1.9%). El eje de tiempo usa las marcas de tiempo del video, asi que los tiempos siguen siendo correctos.
Fotogramas: 2165 | sin borde (descartados): 0 | dudosos: 0
Medidas en pixeles (sin calibrar a mm, a proposito: los videos no tienen todos el mismo aumento).
Archivos en data\processed_data\Video_476:
  serie_temporal_<video>.xlsx
  00_roi_profile_Video_476_EXP5_FAPS5_40V.png
```

### Línea por línea

**`Zona analizada del gel: columnas A a B`**
El programa elige solo un tramo del gel para medir: la parte central y plana, lejos de los anclajes. Las columnas son la posición horizontal en la imagen, en píxeles, contadas desde la izquierda.
- *Normal:* algunos cientos de px. Que sea angosta no es un problema; en 063 son 164 px y el resultado es excelente.
- *Si preguntan "¿por qué no mide todo el gel?":* cerca de los anclajes el gel se ensancha y lo que se deforma ahí depende del anclaje, no de las células. Se mide donde el gel es uniforme.
- *Para verlo:* la figura `00_roi_profile`. La franja verde es la zona elegida.

**`variacion del grosor dentro de la zona: X% (aceptable hasta 6%) -> OK`**
Cuánto cambia el ancho del gel de un extremo al otro de la zona elegida. Es el **chequeo de que la zona es buena**.
- *Normal:* menos de 6 %. En los videos medidos va de 0.3 % a 5.9 %.
- *Si dice NO CUMPLE:* aparece también un AVISO (ver abajo). Mirar `00_roi_profile` antes de creer los números.

**`nota: la camara perdio ~N fotogramas (X%)...`**
Durante la grabación se saltearon algunos fotogramas; es común (1–2 % en casi todos los videos). **No afecta a los resultados**, porque los tiempos salen de las marcas de tiempo que el video guarda para cada fotograma, no de contar fotogramas.
- *Si preguntan:* "la cámara a veces se saltea un cuadro; el programa lo sabe y usa la hora real de cada cuadro".

**`Fotogramas: N | sin borde (descartados): 0 | dudosos: 0`**
Cuántos fotogramas tiene el video y en cuántos no se pudo encontrar el borde del gel.
- *Normal:* 0 y 0.
- Un fotograma sin borde **no se rellena ni se inventa**: queda vacío.
- Si hay más del 1 % aparece el aviso de 2.4.

**`Medidas en pixeles...`**
Siempre aparece. No se convierte a milímetros porque no todos los videos se graban con el mismo aumento. Por eso la cifra principal es un **porcentaje del grosor del gel**, que sí se puede comparar entre videos.

**`Archivos en ...`**
Dónde quedó todo:
- `serie_temporal_<video>.xlsx`: la posición de los dos bordes del gel en cada fotograma.
- `00_roi_profile_...png`: la figura de la zona elegida.

### Avisos posibles de `main.py` (solo aparecen si hay que hacer algo)

| aviso | qué significa | qué hacer |
|---|---|---|
| `el grosor varia X% dentro de la zona (mas del 6% aceptable). Puede que incluya el ensanchamiento cerca de un anclaje` | la zona elegida no es uniforme | mirar `00_roi_profile`; si hace falta, elegir la zona a mano agregando `--x-start A --x-end B` |
| `la zona no incluye la parte mas angosta del gel (la cintura)` | se eligió un tramo raro | mirar `00_roi_profile` |
| `no se encontro una zona plana del gel con el criterio normal; se uso uno mas flojo` | el gel no tiene un tramo uniforme claro (desenfoque, forma rara) | no confiar en los números sin mirar la figura |
| `N% de los fotogramas sin borde o dudosos... Proba de nuevo agregando --half-window 30` | ver 2.4 | repetir con `--half-window 30` |
| `la camara perdio ... y el eje de tiempo se armo con fotograma / fps` | se corrió sin `--base-tiempo pts` | volver a correr con `--base-tiempo pts` |
| `el video no trae marcas de tiempo usables` | el archivo no guarda la hora de cada cuadro | los tiempos pueden estar algo comprimidos si se perdieron cuadros; avisarlo |

### 2.4 Ejemplo con aviso: Video_068 con la configuración de siempre

```
Zona analizada del gel: columnas 391 a 542 (151 px de ancho)
  variacion del grosor dentro de la zona: 0.28% (aceptable hasta 6%) -> OK
  nota: la camara perdio ~44 fotogramas (2.3%). ...
Fotogramas: 1843 | sin borde (descartados): 346 | dudosos: 769
  AVISO: 60% de los fotogramas sin borde o dudosos. Lo mas comun: el gel se mueve mas que la ventana de busqueda (+-15 px). Proba de nuevo agregando --half-window 30.
```

**Qué pasa:** para encontrar el borde, el programa lo busca en una ventana de ±15 px alrededor de donde espera que esté. En 068 el gel se mueve ±10 px todo el tiempo y el punto de partida está corrido, así que en muchos fotogramas el borde queda fuera de esa ventana.
**Qué hacer:** repetir con `--half-window 30`. En 068 eso deja **0** fotogramas sin borde.
**Si preguntan:** "el gel se mueve mucho y el programa lo buscaba en una ventana muy chica; la agrandamos".

---

## 3. Paso 2: `contraction_report.py`

### Ejemplo limpio (Video_476, 6 contracciones estimuladas a 0.1 Hz)

```
==========================================================================
Video_476   (2165 fotogramas, 73.1 s, 30.00 fps)
  las contracciones mueven la franja hacia ABAJO en la imagen
  ruido de fondo de la senal: 0.115 px

  RESULTADO: 6 contracciones  (conteo confiable)
    umbral: 9.4 x ruido, dentro de la zona estable k = 7.1-12.5, con 0 falsos de control
    momentos (s): 11.32, 21.40, 31.36, 41.39, 51.36, 61.36
    tiempo tipico entre eventos: 9.998 s  (0.1000 Hz)
    amplitud mediana: 1.691 px

  RITMO (estimuladas vs espontaneas, por el reloj del estimulador)
    busqueda libre: tren periodico a 0.1000 Hz, no se configuro ninguna frecuencia  [6 de 6 pulsos, p = 0.001]
    periodo: 10.00051 +- 0.00260 s  (0.09999 Hz) | capturados 100% | tren de 11.3 a 61.3 s
    estimuladas: 6 | espontaneas: 0

  CONTRACTILIDAD (estimulados, 6 eventos)
    amplitud: 0.64 % del grosor en reposo  (rango intercuartil 0.634-0.6575 %)
    TTP (inicio -> pico): menos de 155 ms  (2.5 fotogramas)
    RT50 (pico -> 50 % de relajacion): menos de 167 ms  (2.5 fotogramas)
    (con menos de 5 fotogramas no se puede dar un valor, solo un maximo: la contraccion es mas rapida que la camara)

Archivos en data\processed_data\Video_476:
  contracciones_<video>.xlsx
  05_estabilidad_umbral_Video_476.png
  09_contracciones_Video_476.png
  10_ritmo_Video_476.png
  11_cinetica_Video_476.png
```

### Encabezado

**`Video_476 (2165 fotogramas, 73.1 s, 30.00 fps)`**
Duración y velocidad de la cámara. La cámara graba siempre a **30 fotogramas por segundo**, o sea un cuadro cada 33 ms.

**`las contracciones mueven la franja hacia ABAJO / ARRIBA en la imagen`**
Qué se mide: cuando el tejido se contrae, **toda la franja del gel se desplaza** y el programa sigue la posición de su centro. Este renglón dice hacia qué lado se mueve en la pantalla. El programa lo deduce de los datos; no se le dice de antemano.
- *Normal:* ABAJO en 476, 613, 063 y Video_prueba; ARRIBA en 068, 341 y 491. Depende de cómo está montado el gel y de qué lado tira el tejido.
- *Si preguntan "¿por qué no miden cuánto se afina?":* el desplazamiento es mucho más grande y más limpio que el cambio de grosor, que en algunos videos ni siquiera se distingue del ruido.
- Si el reporte es NO REPORTABLE, dice "los eventos mueven..." en vez de "las contracciones".

**`ruido de fondo de la senal: X px`**
Cuánto "tiembla" la medición cuando el gel está quieto: es la vara para decidir qué es una contracción.
- *Normal:* 0.02–0.12 px, una fracción de píxel.
- *Preocupante:* varios px (068 da 3.7 px), porque significa que el gel nunca está quieto. Ver el ejemplo de 068.

### Notas y avisos posibles (debajo del encabezado)

| texto | qué significa | ¿preocupa? |
|---|---|---|
| `nota: N evento(s) muy cerca del principio o del final del video` | ese evento se mide con menos contexto alrededor | no; está marcado en el Excel (columna `junto_al_borde`) |
| `nota: N fotograma(s) dudosos (LOW_QUALITY)` | fotogramas donde el borde se vio peor | poco, si son pocos |
| `AVISO: N fotograma(s) sin medida` | hay huecos sin dato | si son muchos, volver al paso 1 con `--half-window 30` |
| `AVISO: N contraccion(es) con un fotograma sin medida en el pico` | el instante y el tamaño de esa contracción son inciertos | revisarla en el Excel (`junto_a_hueco`) |
| `AVISO: el conteo cambia segun la ventana usada para quitar la deriva` | el resultado depende de un ajuste interno | el conteo sale NO REPORTABLE |
| `AVISO: la ventana ... se fijo a mano mas corta` | solo si alguien usó `--win-s` a mano | no usar `--win-s` |

### `RESULTADO`: el renglón más importante

Hay tres casos posibles:

1. **`RESULTADO: N contracciones (conteo confiable)`**: el número se puede informar.
2. **`RESULTADO: NO REPORTABLE -> motivo`**: el número **no** se informa (ver el ejemplo de 613).
3. **`RESULTADO: no se detectaron contracciones`**: el control salió bien y no hay nada.

**Cómo decide (para explicarlo en simple):** el programa busca picos que sobresalgan del ruido y prueba muchos umbrales, desde 3 hasta 24 veces el ruido. En cada uno hace un **control**: busca picos también en la señal dada vuelta. Una contracción va hacia un solo lado, así que lo que aparece del lado contrario es ruido o vibración (los "falsos de control"). El conteo es confiable solo si existe una **zona estable**: un rango de umbrales donde el número de contracciones no cambia y los falsos son 0. Es la figura `05_estabilidad_umbral`.
- **`umbral: 9.4 x ruido, dentro de la zona estable k = 7.1-12.5, con 0 falsos de control`**: el umbral elegido está en el medio de esa zona. Que la zona sea ancha significa que el resultado no depende del umbral.
- **`(hay otra zona estable con 5 eventos...)`**: aparece en algunos videos (063). Se usa la de umbral más bajo, porque al subir el umbral se empiezan a perder contracciones reales.
- **`momentos (s)`**: cuándo empezó cada contracción, en segundos desde el inicio del video.
- **`tiempo tipico entre eventos`**: la mediana del tiempo entre una contracción y la siguiente. En 476: 10 s = 0.1 Hz, igual que el estimulador.
- **`amplitud mediana: X px`**: cuánto se desplaza la franja, en píxeles. Sirve solo para comparar videos con el mismo aumento. Para comparar entre videos se usa el % de la sección CONTRACTILIDAD.

### `RITMO`: estimuladas vs espontáneas

El estimulador dispara como un reloj (cada 10 s a 0.1 Hz); las contracciones espontáneas no siguen ese reloj. El programa busca un tren de contracciones que caiga sobre ese reloj, dentro de un fotograma de error.
- **`busqueda dirigida a 0.1 Hz`**: se le pasó la frecuencia con `--frecuencia-estimulo`. **`busqueda libre`**: no se le pasó y busca cualquier ritmo regular.
- **`[6 de 6 pulsos, p = 0.001]`**: 6 contracciones cayeron en 6 pulsos posibles del reloj. `p` es la probabilidad de que eso pase por casualidad: **0.001 es el mínimo posible = clarísimo**. Un `p` alto (0.9 en 613) significa que no hay ritmo.
- **`periodo: 10.00051 +- 0.00260 s`**: el período medido con su error. Que dé 10.000 s con un error de 3 ms muestra que el método mide el tiempo con precisión.
- **`capturados 100%`**: el tejido respondió a todos los pulsos. Si da menos, hubo pulsos sin contracción.
- **`estimuladas: 6 | espontaneas: 0`**: la clasificación final.
- **`dudosas`**: (si aparecen) contracciones cerca de un pulso pero un poco corridas, con un tamaño parecido a las del tren.
- **`sacado del tren`**: (si aparece) una contracción que coincide con un pulso por casualidad pero es distinta en tiempo **y** en tamaño. Video_prueba tiene una en 4.82 s.
- Para que haya tren hacen falta al menos 4 contracciones estimuladas.

### `CONTRACTILIDAD`: las cifras a informar

Si hay tren, son las de las **estimuladas**; si no, las de todos los eventos.
- **`amplitud: 0.64 % del grosor en reposo`**: **la cifra principal.** Cuánto se desplaza el gel en cada contracción, como porcentaje de su grosor. Se puede comparar entre videos aunque tengan distinto aumento. Valores medidos: 0.4 % a 2.3 %.
- **`TTP (inicio -> pico)`**: cuánto tarda la contracción en llegar al máximo. **`RT50`**: cuánto tarda en relajarse a la mitad.
- **`menos de 155 ms (2.5 fotogramas)`**: la subida ocurre en 2 o 3 cuadros de cámara, así que el programa **no da un valor inventado**, solo el máximo posible. Para dar un valor hacen falta al menos 5 fotogramas.
- *Si preguntan "¿por qué no da el TTP?":* "la contracción es más rápida que la cámara (30 cuadros por segundo). Para medirlo habría que grabar a 200–300 cuadros por segundo".
- En videos más lentos (466, 583, 491) sí sale un valor, por ejemplo `TTP: 570 ms (mediana de 2 medibles; intervalo [386, 1068] ms)`. El intervalo es el rango donde está el valor verdadero, considerando que la cámara muestrea cada 33 ms.

### `ESTIMULADOR` (solo si se pasó `--frecuencia-estimulo`)

```
ESTIMULADOR (Video_prueba): configurado 0.1 Hz, medido 0.10000 +- 0.000023 Hz -> indistinguible de lo configurado
```

Compara la frecuencia del aparato con la que se midió en el tejido. "Indistinguible" = coinciden.

### Ejemplo NO REPORTABLE (Video_613, vibración)

```
Video_613   (2179 fotogramas, 73.8 s, 30.00 fps)
  los eventos mueven la franja hacia ABAJO en la imagen
  ruido de fondo de la senal: 0.029 px
  nota: 1 evento(s) muy cerca del principio o del final del video: ...

  RESULTADO: NO REPORTABLE -> no hay meseta en el escaneo de k.
    Hay 24 candidatos, pero el control con la senal invertida no permite separarlos del ruido o la vibracion.
    Los tiempos de abajo son para revisar el video, NO para informar.
    momentos (s): 0.39, 1.39, 2.05, ... 71.85
    tiempo tipico entre eventos: 0.667 s  (1.5000 Hz)
    amplitud mediana: 0.320 px

  RITMO (estimuladas vs espontaneas, por el reloj del estimulador)
    busqueda libre: no se encontro un tren periodico que se distinga del azar  [4 de 6 pulsos, p = 0.897]
    estimuladas: 0 | espontaneas: 24   (candidatos: no se informa)

  CONTRACTILIDAD (todos, 24 eventos)
    no se informa: el conteo no es reportable.
```

**Qué pasa:** hay 24 picos hacia un lado y casi la misma cantidad hacia el otro (23 falsos de control), todos al principio y al final del video. Una contracción no va para los dos lados, pero una vibración sí: la imagen entera tiembla (Franco lo confirmó mirando el video). Entre los segundos 5 y 63 la señal es plana.
**Qué informar:** "no hay contracciones detectables". La sensibilidad es de unos 0.2 px, alrededor del 0.1 % del grosor.
**En las figuras:** el título dice en rojo "NO REPORTABLE — candidatos para auditar"; los candidatos van en gris y los falsos de control como triángulos rojos hacia abajo. Si los rojos acompañan a los grises, es vibración o ruido.
- "no hay meseta" = no existe ninguna zona estable del umbral.

### Ejemplo de actividad continua (Video_068, con `--half-window 30`)

```
Video_068_hw30   (1843 fotogramas, 62.5 s, 30.00 fps)
  las contracciones mueven la franja hacia ARRIBA en la imagen
  ruido de fondo de la senal: 3.669 px

  RESULTADO: NO REPORTABLE -> no hay meseta en el escaneo de k.
    Con el umbral de auditoria no queda ningun candidato.
```

**Qué pasa:** la medición está bien (0 fotogramas sin borde). Pero el tejido **nunca se queda quieto**: oscila todo el tiempo (~5–8 px, ~3 veces por segundo) y además tiene unas 21 excursiones grandes e irregulares. El método cuenta contracciones **separadas por reposo**. Como acá no hay reposo, la oscilación continua se toma como "ruido" (3.7 px, cien veces más que en 613) y nada sobresale.
**No es vibración:** se comprobó con un anclaje que se queda quieto.
**Qué informar:** "actividad continua del tejido; el conteo de contracciones no aplica a este video". (Está pendiente una medida de actividad para estos casos; ver la sección 6.)
**Diferencia con 613:** en 613 el ruido es bajísimo y los picos van para los dos lados (vibración). En 068 el ruido es enorme porque el tejido se mueve sin pausa.

---

## 4. Paso 3: `motion_check.py` (opcional)

```
Zona analizada: columnas 981 a 1249. Procesando fotogramas...
  300 fotogramas...
  ...
Listo: 2165 fotogramas a 30.00 fps
==========================================================================
VEREDICTO: ¿el movimiento medido por bordes (center_px) se confirma midiendo
           la imagen entera por otro metodo (intensidad)?
  tamano: 0.82 veces (1 = igual) | forma: correlacion 0.91 (1 = identica)
  -> CONFIRMA: los dos metodos ven el mismo movimiento (forma y tamano).
==========================================================================
Archivos en data\processed_data\Video_476:
  movimiento_<video>.xlsx
  07_movimiento_<video>.png
```

Es una segunda opinión: mide el desplazamiento comparando la imagen entera entre fotogramas, sin usar los bordes.
- **`tamano`**: cuánto mide este método respecto del principal. Cerca de 1 es bueno; se acepta entre 0.8 y 1.2.
- **`correlacion`**: si los dos ven la misma forma en el tiempo. 0.9 o más es bueno.
- **Tres veredictos posibles:**
  - **CONFIRMA**: los dos métodos coinciden.
  - **Coinciden en forma pero no en tamaño**: revisar.
  - **AVISO: NO confirma**: mirar el video (vibración, desenfoque, borde mal medido).
- `AVISO: la medida ... solo funciona en el X% de los fotogramas`: al gel le falta textura para este método; ese canal no sirve en ese video.
- *Valores medidos:* 0.82–0.99 de tamaño en todos los videos probados.

---

## 5. Preguntas típicas y qué contestar

- **"¿Por qué en píxeles y no en micras?"** Los videos no tienen todos el mismo aumento. Por eso la cifra principal es en % del grosor del gel.
- **"¿Cómo sabe que es una contracción y no ruido?"** Hace el mismo análisis sobre la señal dada vuelta; ahí no puede haber contracciones. Si aparecen picos parecidos, no se informa nada.
- **"¿Por qué MuscleMotion da otro número?"** MuscleMotion mide cambios de brillo, y el brillo cambia también por la compresión del video o por la luz. Este método mide dónde está el borde del gel. En 476, MuscleMotion ve ~90 picos que vienen de la compresión del video, no del tejido.
- **"¿Qué es k?"** El umbral medido en veces el ruido: k = 9 significa que el pico tiene que ser 9 veces más grande que el temblor normal de la medición.
- **"¿Y si sale NO REPORTABLE?"** Mirar el video y la figura `09_contracciones`:
  - picos hacia los dos lados → vibración (613)
  - movimiento sin pausas → actividad continua (068)
  - nada → no hay contracciones

---

## 5b. Conceptos que cuestan (explicados de cero)

**¿Cómo se "pierden" fotogramas?** La cámara saca 30 fotos por segundo y la computadora las va guardando. Si en un momento está ocupada (disco, procesador), no llega a guardar una y esa foto se pierde. Pasa en la grabación, no en el microscopio, y al mirar el video no se nota.

**¿Qué es "fotograma / fps"?** Una forma de calcular en qué segundo se sacó cada foto: contar fotos y dividir por 30. La foto 300 sería el segundo 10. Funciona solo si no se perdió ninguna: si se perdieron 10 antes, la foto 300 es del segundo 10.33. El error se acumula y las contracciones parecen más juntas de lo que fueron (Video_466 daba un período de 9.5 s en vez de 10). Por eso usamos las **marcas de tiempo** que el archivo guarda junto a cada foto (`--base-tiempo pts`): con ellas, perder fotos no cambia los tiempos.

**¿Qué son los falsos de control?** Una contracción mueve el gel hacia **un** lado. El ruido y las vibraciones lo mueven hacia los **dos** lados por igual. El programa busca picos con el mismo criterio hacia los dos lados:
- del lado de las contracciones encuentra contracciones más ruido;
- del lado contrario ("la señal dada vuelta") solo puede encontrar ruido.

Lo que aparece del lado contrario son los falsos de control: miden cuánto ruido se cuela con ese umbral. Por ejemplo, 6 hacia abajo y 0 hacia arriba quiere decir que las 6 son reales. 24 hacia abajo y 23 hacia arriba (613) quiere decir que es vibración.

**¿Y si la contracción rebota un poco hacia el otro lado?** No se modela aparte, pero no hace falta. Para contar, un pico tiene que superar el umbral, unas 9 veces el ruido. En 476 el rebote mide 0.3–0.5 px y el umbral es de 1.08 px, así que no llega. Si un rebote fuera grande, aparecería como falso de control y el conteo saldría NO REPORTABLE. El error va siempre hacia "no informar", nunca hacia inventar contracciones.

**¿Qué es el rango intercuartil?** Se ordenan los eventos de menor a mayor y se dejan afuera el 25 % más chico y el 25 % más grande. Lo que queda es el intervalo donde cae el 50 % del medio. Si es angosto (476: 0.634–0.658 %), las contracciones son todas parecidas.

**¿Por qué "TTP menos de X ms"?** La cámara mira cada 33 ms, como si parpadeara. En 476 toda la subida ocurre entre 2 o 3 fotos. No sabemos si la contracción arrancó justo después de una foto ni si el máximo verdadero cayó entre dos fotos. Lo único seguro es que la subida duró **como mucho** unos 3 intervalos (100–155 ms). Pudo durar 60 o 120 ms, y con esta cámara no se puede distinguir. Por eso se da el máximo y no un valor. Para dar un valor exigimos al menos 5 fotos en la subida. El RT50 (del máximo a la mitad de la relajación) tiene el mismo problema.

**¿Qué es `junto_al_borde`?** Antes de buscar picos se calcula la posición de reposo de cada momento, mirando unos segundos antes y después. En el primer o el último segundo del video falta el "antes" (o el "después"), así que el reposo se calcula con la mitad de datos y es menos preciso. El evento se cuenta igual; solo queda marcado. Ejemplo: el de 063 en 0.31 s, que es real.

**¿Qué es un fotograma sin medida?** Uno donde no se encontró el borde del gel (por ejemplo, porque el gel salió de la zona donde se lo busca, como en 068). No se inventa un valor: queda vacío, no cuenta para el ruido y no puede ser un pico.

**¿Qué es la deriva y la "ventana para quitarla"?** La deriva es un corrimiento lento que no es contracción: el gel se asienta, el foco cambia un poco. Se quita restando la posición de reposo, calculada con una ventana de unos segundos. El largo de esa ventana es una elección, así que el programa cuenta tres veces: con la ventana más corta, normal y más larga. Si las tres dan lo mismo, el resultado no depende de esa elección. Si cambia, el conteo no se informa.

**¿Qué es la "compresión del video" y por qué engaña a MuscleMotion?** Un `.mp4` no guarda cada foto entera, porque pesaría muchísimo:
- cada tantas fotos guarda una completa (la "foto clave");
- en las del medio guarda solo lo que cambió.

Al reconstruir la imagen, el brillo da un pequeño salto en cada foto clave. En 476 pasa cada 5 fotos exactas, también en el fondo vacío. MuscleMotion mide cambios de brillo y cuenta esos saltos como movimiento: unos 90 picos falsos. Nuestro método mide dónde está el borde del gel, y un cambio de brillo parejo no lo mueve.

---

## 6. Pendiente: hacer el programa más amigable para quien no programa

Hoy hay que copiar comandos y cambiar el nombre del video a mano. Ideas, de menor a mayor esfuerzo:

0. **Hecho (2026-10-07): `interfaz.py` + `Analizar.bat`** (sección 0).
1. **Un solo comando que corra todo** (`analizar.py --video Video_XXX [--frecuencia 0.1]`): hace los pasos 1 y 2, y el 3 si se pide. Busca el video solo en `data\raw_videos\` (sin escribir la ruta). Si detecta muchos fotogramas sin borde, repite solo con `--half-window 30`.
2. **Procesar una carpeta entera** y armar una tabla resumen con una fila por video: conteo, reportable sí/no, frecuencia, amplitud %, TTP/RT50. Ya estaba en la lista como "script por lotes".
3. **Un informe por video en una página** (HTML o PDF) con el resultado en palabras simples y las figuras principales, para mandar al equipo sin abrir los Excel.
4. **Doble clic en vez de consola:** un archivo `.bat` que pregunte el nombre del video y la frecuencia, o una ventanita simple para elegir el video, escribir la frecuencia y apretar "Analizar".
5. **Configuración en un archivo** (por ejemplo `config.txt` con frecuencia, `half-window`, etc.) para no tocar comandos ni código.

Ninguna cambia números: solo envuelven los scripts actuales.
