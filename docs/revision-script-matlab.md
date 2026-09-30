# Revisión del script `Contraction_Analysis.mlx`

Fecha 2026-09-30. Revisión hecha al evaluar si portar estas métricas al
pipeline de Python. El script es de Andrés Felipe Zemanate-Largo y calcula
TTP, RT50, amplitud, cambio relativo y P2P a partir de un `contraction.txt`.

**La idea del script está bien y las métricas son las correctas** — son las
que definen los dos papers del grupo. Lo que sigue son cosas de la
implementación que conviene resolver antes de usar los números para comparar
muestras. Cada una va con el arreglo.

---

## 1. No hay umbral de amplitud: todo máximo local es un pico

    [Peak, Position] = findpeaks(Amplitude_Detrend, 'MinPeakDistance', Min_Peak_Distance);

La descripción dice que los picos se identifican "using a prominence-based
criterion, which ensures that only physiologically relevant contractions are
detected", pero la llamada no pasa `MinPeakProminence` ni `MinPeakHeight`.
El único filtro es la separación mínima.

Consecuencia: `findpeaks` devuelve **el máximo local de cada ventana de 520
muestras, siempre**, haya contracción o no. Sobre una señal plana con ruido
devuelve un pico cada 520 muestras igual.

*Arreglo:* pasar `MinPeakProminence` como dice la descripción, y elegir el
valor con un barrido, no a ojo (ver punto 8).

## 2. `Half_Relax_Time` no calcula RT50

    % Target: 50% decay from peak toward offset point
    Half_Relax_Time(i) = (Time(Off) - Time(P)) * 0.5;

El comentario dice lo correcto, el código hace otra cosa: **la mitad de la
duración total de la relajación**, no el tiempo hasta caer al 50 % de la
amplitud. Sólo coinciden si la relajación fuera perfectamente lineal, y no lo
es — decae de forma aproximadamente exponencial.

*Arreglo:* buscar el primer índice después del pico donde la señal cruza
`Amplitude(On) + 0.5 * (Amplitude(P) - Amplitude(On))`, e interpolar entre esa
muestra y la anterior para ganar resolución sub-fotograma.

## 3. El cambio relativo divide por un número que oscila alrededor de cero

    Peak_Change(i) = ((Amplitude_Detrend(P) - Amplitude_Detrend(On)) / Amplitude_Detrend(On));

`Amplitude_Detrend` viene de `detrend(Amplitude, 1)`, o sea la señal ya
centrada en cero. En el onset su valor es esencialmente ruido, así que el
denominador puede ser 0.01 o −0.03 y el porcentaje sale disparado o cambia de
signo sin que pase nada físico.

*Arreglo:* dividir por la línea de base **cruda**, `Amplitude(On)`, que es la
que tiene una escala real.

## 4. Corrimiento de −5 muestras sin justificación

    Idx_Before = Idx_Before - 5;

Corre todos los onsets cinco muestras hacia atrás. No hay comentario ni
mención en la descripción. A 30 fps son **167 ms sumados a cada TTP**. En una
contracción con TTP real de 300 ms eso es un sesgo del 55 %; en una de 67 ms
el TTP resultante es mayormente el corrimiento.

*Arreglo:* si la intención era compensar que el cruce de la línea de base
llega tarde, la forma correcta es definir el onset como el cruce del 10 % de
la amplitud (criterio estándar) en vez de un desplazamiento fijo.

## 5. `Min_Peak_Distance = 520` hardcodeado

    %Min_Peak_Distance = round((10/(Time(2)-Time(1)))*0.8);
    Min_Peak_Distance = 520;

La versión paramétrica está comentada justo arriba. A 30 fps, 520 muestras son
17.3 s de separación mínima: con estimulación a 0.1 Hz (un latido cada 10 s)
**fusiona latidos consecutivos** y se pierde uno de cada dos.

*Arreglo:* descomentar la línea paramétrica, que calcula la separación a
partir del período esperado y del intervalo de muestreo real.

## 6. `Data(1:2000, :)` descarta el final de los archivos largos

    Time = Data(1:2000,1)/1000;
    Amplitude = Data(1:2000,2);

Toma las primeras 2000 muestras y tira el resto. Varios de nuestros archivos
son más largos: el `contraction.txt` de Video_268 tiene 2250 muestras, así que
se pierden **250 fotogramas, unos 8 segundos de video**, en silencio. Si hay
una contracción ahí, no se cuenta.

A eso se suman `Starting_Trim = 140` y `Ending_Trime = 100`, también fijos.

*Arreglo:* usar `Data(:,1)` y `Data(:,2)`, y hacer el recorte por tiempo
(segundos) en vez de por número de muestra.

## 7. Corre sobre la salida de MuscleMotion, cuya base de tiempo está comprimida

El script lee `contraction.txt`, que es la señal de MuscleMotion. Medimos que
**ImageJ importa menos fotogramas que OpenCV** en los cinco videos de la
carpeta `OK`:

| video | MuscleMotion | OpenCV / ffprobe | déficit |
|---|---|---|---|
| Video_063 | 1836 | 1848 | 0.65 % |
| Video_268 | 2250 | 2283 | 1.45 % |
| **Video_466** | **1992** | **2076** | **4.05 %** |
| Video_491 | 1822 | 1846 | 1.30 % |
| Video_583 | 2204 | 2236 | 1.43 % |

OpenCV coincide exactamente con el conteo de paquetes de `ffprobe`. Como
MuscleMotion arma su eje temporal como `fotograma / 30`, ese déficit comprime
su escala de tiempo por un factor que **depende de cada archivo**, entre
0.65 % y 4.05 %. Todo TTP y RT50 calculado sobre esa señal hereda ese error, y
como cambia de video a video **no se cancela al comparar muestras**.

Detalle completo en `claude/base-de-tiempo-y-frames-perdidos.md`.

*Arreglo:* calcular las métricas sobre la señal del pipeline de Python
(`center_px`), cuyo eje temporal sale de los timestamps del contenedor.

## 8. No hay control de falsos positivos

No es un error, es algo que falta y que cambia bastante la confianza en los
números. Tal como está, no hay forma de saber si un pico detectado es una
contracción o ruido.

*Arreglo:* el control que usamos nosotros es barato: correr el mismo detector
sobre la señal **invertida**. Una contracción sólo puede ir en un sentido, así
que todo lo que aparece del lado invertido es ruido. Y barrer el umbral: si el
conteo tiene una **meseta** (no cambia al subir el umbral) con cero falsos,
los eventos son reales.

---

# Lo más importante: el muestreo es más lento que el evento

Esto no es un problema del script sino de la adquisición, y afecta a
cualquier implementación, la de MATLAB y la nuestra por igual.

Medimos la cinética real sobre el promedio de eventos alineados de cada video
(ruido del promedio 0.03 px):

| video | amplitud | TTP | subida 10–90 % |
|---|---|---|---|
| Video_prueba | 6.14 px | 67 ms (**2 fotogramas**) | 33 ms (**1 fotograma**) |
| Video_063 | 1.49 px | 67 ms (**2 fotogramas**) | 33 ms (**1 fotograma**) |
| Video_268 | 1.55 px | 67 ms (**2 fotogramas**) | 33 ms (**1 fotograma**) |
| Video_466 | 4.33 px | 300 ms (9 fr) | 100 ms (3 fr) |
| Video_583 | 3.07 px | 300 ms (9 fr) | 133 ms (4 fr) |

La forma cruda del evento promedio de Video_prueba, en múltiplos del ruido:

    fotograma:  -3   -2   -1    0   +1   +2   +3   +4
    señal:      -0    1  147  190  146   77   31   10

Pasa de ruido a 147 sigma **en un fotograma**. La contracción entera dura
cuatro.

En ese caso, un TTP de "67 ms" no describe la muestra: describe la cámara. Si
la contracción durara 20 ms o 60 ms, el número saldría igual. Se puede afirmar
**TTP < 67 ms**, y eso es información legítima, pero no se puede tabular
67 ms y comparar muestras con ese número.

Es coherente con la fisiología: el twitch de músculo esquelético tiene un TTP
típico de 30–80 ms, y la cámara muestrea cada 33 ms. Video_466 y Video_583
responden mucho más lento (300 ms, con meseta), compatible con una respuesta
fusionada o con la mecánica del gel más que con el twitch.

**Para medir TTP y RT50 de un twitch hacen falta unas 10 muestras en la
subida, o sea 200–300 fps.** Es la única forma de que estas métricas midan
biología y no el intervalo de muestreo.

Ver la figura `docs/metricas_cinetica.png`.

---

## Resumen para la conversación con el equipo

1. Las métricas elegidas son las correctas y vale la pena tenerlas.
2. Seis cosas del script conviene arreglarlas antes de comparar muestras; las
   más serias son el RT50 mal definido, el corrimiento de −5 y la falta de
   umbral de amplitud.
3. Calcularlas sobre MuscleMotion mete un error de escala temporal que cambia
   de archivo en archivo.
4. **Y la pregunta de fondo no es de software:** a 30 fps, TTP y RT50 no son
   medibles en las muestras rápidas. Si esas métricas importan para el
   trabajo, hay que filmar un subconjunto a 200–300 fps.
