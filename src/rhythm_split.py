"""
rhythm_split.py
----------------
Separa contracciones ESTIMULADAS de ESPONTANEAS, y mide la frecuencia del
estimulo con su incertidumbre.

EL CRITERIO NO ES LA AMPLITUD NI LA VENTANA TEMPORAL
-----------------------------------------------------
Es tentador separarlas por tamano ("las estimuladas son mas grandes") o por
tiempo ("primero las espontaneas, despues el tren estimulado"). Las dos cosas
fallan: con estimulacion debil las amplitudes se solapan, y las espontaneas
pueden seguir apareciendo DURANTE el tren estimulado.

La propiedad que define a una contraccion estimulada es otra, y es la unica
que no depende del montaje:

    esta ENGANCHADA EN FASE a un reloj periodico.

El equipo estimulante dispara en instantes  t = fase + n * T  con n entero.
Las espontaneas no saben nada de ese reloj: sus tiempos caen donde caen. Asi
que el problema es encontrar la grilla (T, fase) que mejor explica un
subconjunto de los eventos, y llamar espontaneo a todo lo que quede afuera.

COMO SE BUSCA LA GRILLA
------------------------
1. Se barre un rango de periodos candidatos T. Con la frecuencia configurada
   (`--frecuencia-estimulo`), solo entre 0.9 y 1.1 veces su periodo (busqueda
   DIRIGIDA, una por frecuencia). Sin ella, de 0.3 s a ~1/3 del registro
   (busqueda LIBRE, un tren). El paso entre candidatos se ajusta a la
   tolerancia, para que ninguna ranura se corra mas de media tolerancia.
2. Para cada T se prueba, como origen de fase, el instante de cada evento (el
   optimo siempre se puede anclar en un evento) y se cuenta cuantas RANURAS de
   la grilla quedan ocupadas por algun evento a menos de 2 fotogramas.
3. Se puntua con un z-score contra lo que daria el azar:

       z = (ranuras_ocupadas - esperado) / sqrt(varianza)

   con el esperado calculado a partir de la densidad de eventos en la ventana.
   Gana el mejor z, salvo que un candidato casi igual de bueno sea multiplo x2
   o x3 del ganador (entonces el ganador era un armonico). Ademas se exige que
   el 75 % de las ranuras esten ocupadas (`min_captura`).
4. El T ganador se limpia (tolerancia atada al jitter medido; R5: sale quien
   falla en tiempo Y en amplitud) y se refina por minimos cuadrados, lo que da
   T con error estandar.

El instante de cada evento es el INICIO de la contraccion (cruce del 10 %),
no el pico: en los eventos con meseta el pico lo decide el ruido.

VALIDACION: LAS LISTAS DE INSTANTES AL AZAR (Monte Carlo)
---------------------------------------------------------
El buscador SIEMPRE encuentra algun tren: entre 29 instantes cualesquiera hay
algun ritmo en el que 5 o 6 caen alineados. La pregunta es si el tren
encontrado es mejor que lo que arma el azar. Para responderla, en CADA
corrida (en memoria, no se guarda nada):

  1. se sortean tantos instantes al azar como eventos tiene el video, en el
     mismo tramo, sin ningun reloj detras (con el refractario observado);
  2. se les corre LA MISMA busqueda y se anota el z del mejor tren;
  3. se repite 1000 veces (semilla fija: dos corridas dan lo mismo);
  4. p = fraccion de listas al azar con z >= el del video (estimador (k+1)/(n+1),
     asi que el minimo es 1/1001). Se exige p <= 0.01.

Como al azar se le aplica la misma busqueda que al video, el p ya tiene en
cuenta cuantos periodos se probaron. Por eso la busqueda dirigida tiene mas
poder: al probar pocos periodos el azar tiene pocos intentos. Medido con
espontaneas a ~0.3 por segundo y 6 latidos estimulados: la busqueda libre no
confirmaba el tren en 6 de 20 series; la dirigida, en 0 de 20.

LA FRECUENCIA DE LAS ESPONTANEAS NO ES UN NUMERO
-------------------------------------------------
Las contracciones espontaneas de estas celulas no mantienen una frecuencia
constante. Reportar "la frecuencia espontanea" como un solo valor es
enganoso. Este modulo devuelve la mediana y el rango intercuartil de los
intervalos, y ademas la frecuencia INSTANTANEA evento a evento, que es lo que
hay que graficar para ver como deriva.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.estadistica import mad

# Fase 3 (grupo 1): constantes del ritmo. Ver claude/propuesta-fase-3-ritmo-cinetica.md
TOL_BUSQUEDA_FRAMES = 2      # tolerancia de la busqueda: 2 fotogramas (antes 3)
TOL_MULTIPLO = 0.03          # cuanto puede apartarse T2/(2*T1) de 1 para ser "multiplo"
AMP_COMPATIBLE = (0.5, 2.0)  # amplitud compatible con el tren: 0.5-2x la mediana
VENTANA_DIRIGIDA = 0.10      # busqueda dirigida: +-10 % del periodo configurado
N_SIMULACIONES = 1000        # Monte Carlo: con 200 el p minimo es 0.005


# ---------------------------------------------------------------------------
# nucleo: encontrar la grilla periodica
# ---------------------------------------------------------------------------

def _contar_vectorizado(t, periodos, tols, bloque=200):
    """Para cada periodo, cuantos eventos caen en la mejor grilla, y su ancla.

    Version vectorizada del barrido. El optimo de la fase siempre se puede
    anclar en el instante de algun evento, asi que se prueban todos los
    eventos como origen a la vez: con D[i,j] = t_i - t_j, el residuo de i
    respecto de la grilla anclada en j es D[i,j] - round(D[i,j]/T)*T.

    Se hace en bloques de periodos para no construir un tensor gigante. Sin
    esto el Monte Carlo no es viable: son cientos de barridos completos.
    """
    D = t[:, None] - t[None, :]                      # (N, N)
    n_p = len(periodos)
    mejores = np.zeros(n_p, dtype=int)
    anclas = np.zeros(n_p, dtype=int)
    for a in range(0, n_p, bloque):
        b = min(a + bloque, n_p)
        T = periodos[a:b][:, None, None]
        tol = tols[a:b][:, None, None]
        resid = D[None, :, :] - np.round(D[None, :, :] / T) * T
        cerca = np.abs(resid) <= tol                  # (P, i, j)
        cuentas = cerca.sum(axis=1)                   # (P, j)
        mejores[a:b] = cuentas.max(axis=1)
        anclas[a:b] = cuentas.argmax(axis=1)
    return mejores, anclas


def _asignar(t, T, t0, tol):
    """Eventos asignados a la grilla anclada en t0, un evento por ranura."""
    n = np.round((t - t0) / T)
    resid = t - (t0 + n * T)
    idx = np.flatnonzero(np.abs(resid) <= tol)
    if len(idx) == 0:
        return idx, np.array([], int)
    # Si dos eventos caen en la misma ranura, se queda el mas cercano al
    # centro: uno de los dos es un espontaneo que coincidio por casualidad.
    orden = idx[np.argsort(np.abs(resid[idx]))]
    vistos, elegidos = set(), []
    for i in orden:
        r = int(n[i])
        if r not in vistos:
            vistos.add(r)
            elegidos.append(i)
    elegidos = np.array(sorted(elegidos), dtype=int)
    return elegidos, n[elegidos].astype(int)


def _z_periodicidad(n_ocupadas: int, n_ranuras: int, densidad: float, tol: float) -> float:
    """Cuanto se aparta del azar que `n_ocupadas` de `n_ranuras` esten llenas.

    Bajo un proceso sin estructura periodica con densidad `densidad`
    (eventos por segundo), la probabilidad de que una ranura dada tenga algun
    evento a menos de `tol` es 1 - exp(-densidad * 2 * tol).
    """
    if n_ranuras < 1:
        return 0.0
    p = 1.0 - np.exp(-densidad * 2.0 * tol)
    p = min(max(p, 1e-9), 1 - 1e-9)
    esperado = n_ranuras * p
    var = n_ranuras * p * (1 - p)
    return float((n_ocupadas - esperado) / np.sqrt(max(var, 1e-12)))


def buscar_grilla(tiempos: np.ndarray, duracion_s: float,
                  periodo_min: float = 0.3, periodo_max: float | None = None,
                  n_candidatos: int = 600, tol_s: float = 0.10,
                  min_eventos: int = 4,
                  min_captura: float = 0.75) -> dict | None:
    """Busca el tren periodico que mejor explica un subconjunto de los eventos.

    `min_captura` es lo que impide caer en un ARMONICO, y hace falta: el
    z-score solo no alcanza. Si el periodo real es T, la grilla de T/2 tambien
    contiene todos los eventos verdaderos, pero con la mitad de las ranuras
    vacias; la de T/3, con dos tercios vacias. Como esas grillas tienen mas
    ranuras, pueden acumular un z mayor que la verdadera aunque expliquen los
    datos peor. Verificado sobre Video_prueba: sin este requisito el buscador
    devolvia T = 3.362 s, que es exactamente un tercio del periodo real de
    10.087 s, con 44 % de captura.

    Exigir que la mayoria de las ranuras esten ocupadas elimina T/2 (<=50 %),
    T/3 (<=33 %) y siguientes, y no molesta al periodo verdadero, donde la
    estimulacion electrica captura casi todos los pulsos.

    Cuidado: una preparacion con bloqueo 2:1 real captura el 50 % de los
    pulsos. En ese caso el tren fisiologico ES el de 2T y el metodo lo
    reporta asi, que es lo correcto; pero si se sospecha bloqueo y se quiere
    ver la grilla del estimulador, hay que bajar `min_captura`.
    """
    t = np.sort(np.asarray(tiempos, float))
    if len(t) < min_eventos:
        return None
    span = float(t[-1] - t[0])
    if periodo_max is None:
        periodo_max = span / max(min_eventos - 1, 2)
    if periodo_max <= periodo_min:
        return None

    # La grilla de periodos tiene que ser lo bastante fina para la tolerancia:
    # si dos candidatos vecinos difieren en dT, a `span` segundos del ancla las
    # ranuras se corren span*dT/T. Con 600 candidatos fijos el paso cerca de
    # 10 s era de 0.07 s y, a 5 periodos del ancla, las ranuras se corrian
    # 0.18 s: con la tolerancia de 2 fotogramas (67 ms) el tren real de
    # Video_prueba no entraba entero en ningun candidato. Se exige que el
    # corrimiento en el extremo sea <= tol/2 en el peor caso (Fase 3).
    n_fino = int(np.ceil(np.log(periodo_max / periodo_min) * span / max(tol_s, 1e-6)))
    periodos = np.geomspace(periodo_min, periodo_max, max(n_candidatos, n_fino))
    # TOLERANCIA ABSOLUTA, no una fraccion del periodo. Esto importa mucho y
    # la primera version lo tenia al reves. El jitter de un estimulador
    # electrico es un numero fijo de milisegundos, no un porcentaje: no es mas
    # impreciso por disparar cada 10 s que cada 1 s. Con una tolerancia
    # proporcional, un periodo largo exige coincidencias flojas (0.2 s con
    # T = 10 s) y por eso su z sale castigado frente a grillas cortas y
    # espurias. Verificado en simulacion: con tolerancia proporcional el
    # buscador elegia una grilla falsa de 4.63 s armada con espontaneas en vez
    # del tren real de 10 s.
    tols = np.full_like(periodos, float(tol_s))

    cuentas, anclas = _contar_vectorizado(t, periodos, tols)
    cand = np.flatnonzero(cuentas >= min_eventos)
    if len(cand) == 0:
        return None

    # Puntaje de TODOS los candidatos a la vez (antes, un bucle de Python por
    # candidato; con la grilla fina eran ~2400 por busqueda y el Monte Carlo
    # tardaba minutos). Mismas cuentas que `_asignar`: un evento por ranura.
    T = periodos[cand][:, None]
    tol = tols[cand][:, None]
    t0 = t[anclas[cand]][:, None]
    S = np.round((t[None, :] - t0) / T)
    R = np.abs(t[None, :] - (t0 + S * T))
    M = R <= tol                                            # (K, N)
    grande = np.iinfo(np.int64).min // 4
    Sm = np.where(M, S, grande).astype(np.int64)
    ultimo = np.maximum.accumulate(Sm, axis=1)
    previo = np.concatenate([np.full((len(cand), 1), grande, np.int64), ultimo[:, :-1]], axis=1)
    repetida = M & (previo == Sm)                           # misma ranura que el anterior
    n_ocup = (M & ~repetida).sum(axis=1)
    filas = np.arange(len(cand))
    s_ini = S[filas, M.argmax(axis=1)]
    s_fin = S[filas, M.shape[1] - 1 - M[:, ::-1].argmax(axis=1)]
    # Si dos eventos comparten la primera (o la ultima) ranura, `_asignar` se
    # queda con el mas cercano al centro: el tramo del tren empieza ahi.
    i_ini = np.where(M & (S == s_ini[:, None]), R, np.inf).argmin(axis=1)
    i_fin = np.where(M & (S == s_fin[:, None]), R, np.inf).argmin(axis=1)
    n_ran = (s_fin - s_ini).astype(int) + 1
    ok = (n_ocup >= min_eventos) & (n_ocup >= min_captura * n_ran)   # primer filtro anti-armonico
    if not ok.any():
        return None
    dur = np.maximum(t[i_fin] - t[i_ini], 1e-9)
    dens = (i_fin - i_ini + 1) / dur
    pr = np.clip(1.0 - np.exp(-dens * 2.0 * tol[:, 0]), 1e-9, 1 - 1e-9)
    z = (n_ocup - n_ran * pr) / np.sqrt(np.maximum(n_ran * pr * (1 - pr), 1e-12))

    validos = [{"k": int(k), "T": float(periodos[k]), "z": float(zz)}
               for k, zz in zip(cand[ok], z[ok])]

    def _completar(v):
        k = v["k"]
        Tk, tolk = float(periodos[k]), float(tols[k])
        idx, ranuras = _asignar(t, Tk, t[anclas[k]], tolk)
        return {"T": Tk, "fase": float(t[anclas[k]]), "tol": tolk, "z": v["z"],
                "idx": idx, "ranuras": ranuras,
                "n_ocupadas": len(idx), "n_ranuras": int(ranuras[-1] - ranuras[0]) + 1,
                "t_inicio": float(t[idx[0]]), "t_fin": float(t[idx[-1]])}

    # SEGUNDO filtro anti-armonico (Fase 3, H38). Gana el MEJOR PUNTAJE, salvo
    # que haya un candidato casi tan bueno (z >= 90 % del maximo) en un MULTIPLO
    # x2 o x3 del ganador: entonces el ganador era un armonico (T/2, T/3) armado
    # con espontaneas que llenaron las ranuras intermedias, y se sube al
    # multiplo. Antes la regla era "entre los casi-mejores, el periodo mas
    # largo", y eso empujaba al borde del rango: con espontaneas densas elegia
    # periodos falsos (T = 10.96 s en lugar de 10.00 s) y perdia latidos reales
    # (165 de 360 en el sintetico denso, contra 33 con esta regla).
    z_max = max(v["z"] for v in validos)
    mejor = max(validos, key=lambda v: v["z"])
    for _ in range(4):
        sube = [v for v in validos if v["z"] >= 0.90 * z_max and any(
            abs(v["T"] / (m * mejor["T"]) - 1.0) <= TOL_MULTIPLO for m in (2, 3))]
        if not sube:
            break
        mejor = max(sube, key=lambda v: v["z"])
    return _completar(mejor)


def _theil_sen(n: np.ndarray, y: np.ndarray):
    """Ajuste ROBUSTO de y = fase + T*n: mediana de las pendientes de a pares.

    Hace falta y no es un lujo. El evento colado que mas dano hace es el que
    cae en un EXTREMO del tren: en minimos cuadrados tiene el maximo brazo de
    palanca, inclina toda la recta, reparte su error entre todos los residuos
    y con eso se vuelve indetectable. Medido sobre Video_prueba: un espontaneo
    en t=4.37 s tomado como primera ranura movia el periodo de 10.091 s a
    10.127 s y dejaba todos los residuos por debajo de 0.3 s, asi que ninguna
    pasada de limpieza lo sacaba.

    Theil-Sen no tiene ese problema: una minoria de puntos malos no mueve la
    mediana de las pendientes, y el intruso queda expuesto como un residuo
    grande.
    """
    n = np.asarray(n, float)
    y = np.asarray(y, float)
    i, j = np.triu_indices(len(n), k=1)
    dn = n[j] - n[i]
    ok = dn != 0
    if not ok.any():
        return float("nan"), float("nan")
    T = float(np.median((y[j][ok] - y[i][ok]) / dn[ok]))
    fase = float(np.median(y - T * n))
    return T, fase


def _refinar(t_asignados: np.ndarray, ranuras: np.ndarray):
    """Ajusta t = fase + ranura * T por minimos cuadrados.

    Devuelve (T, error estandar de T, fase, jitter = desvio de los residuos).
    Es el paso que convierte "el periodo esta cerca de 10 s" en un numero con
    incertidumbre, que es lo que se puede comparar contra el equipo.
    """
    n = np.asarray(ranuras, float)
    y = np.asarray(t_asignados, float)
    if len(n) < 3:
        return float("nan"), float("nan"), float("nan"), float("nan")
    A = np.vstack([n, np.ones_like(n)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    T, fase = float(coef[0]), float(coef[1])
    resid = y - (fase + T * n)
    gl = len(n) - 2
    s2 = float(resid @ resid) / gl if gl > 0 else float("nan")
    Sxx = float(np.sum((n - n.mean()) ** 2))
    err_T = float(np.sqrt(s2 / Sxx)) if (Sxx > 0 and np.isfinite(s2)) else float("nan")
    # Jitter ROBUSTO (MAD), no desvio estandar: la segunda pasada usa este
    # numero para decidir a quien suelta, y si un solo evento espontaneo colado
    # lo infla, la tolerancia se agranda y ese evento nunca se va. Con MAD, un
    # intruso no mueve la escala y queda expuesto como residuo grande.
    jitter = mad(resid) if len(resid) > 1 else float("nan")
    return T, err_T, fase, jitter


# ---------------------------------------------------------------------------
# validacion por Monte Carlo
# ---------------------------------------------------------------------------

def _z_nulo(tiempos: np.ndarray, duracion_s: float, n_sim: int, rng, **kw) -> np.ndarray:
    """Distribucion del z MAXIMO cuando no hay enganche de fase.

    NO se permutan los intervalos. Esa fue la primera version y esta MAL:
    si los eventos ya son casi equiespaciados, permutar sus intervalos
    devuelve practicamente la misma serie, el nulo queda identico a los datos
    y el p-valor se va a 1. O sea que el caso mas comun y mas facil -- un tren
    estimulado limpio, sin espontaneas -- daba "no hay estimulacion".
    Verificado en simulacion: 0/10 detecciones sobre trenes perfectamente
    regulares.

    El nulo correcto para la pregunta "estan enganchados a un reloj?" es
    tiempos SIN estructura temporal: se sortean uniformes en la misma ventana,
    con el mismo numero de eventos, imponiendo el periodo refractario
    observado (el intervalo minimo real) para no generar rafagas imposibles.
    Se corre el MISMO buscador, asi que el p-valor ya incluye el haber probado
    muchos periodos y el haber elegido la ventana post-hoc.

    Consecuencia honesta de este cambio: una serie ESPONTANEA muy regular
    tambien va a dar significativa, porque de hecho esta enganchada a algo. La
    distincion entre "estimulado" y "espontaneo pero muy regular" no se puede
    hacer solo con los tiempos; ahi hay que mirar la amplitud y saber si el
    estimulador estaba encendido.
    """
    t = np.sort(np.asarray(tiempos, float))
    n = len(t)
    t0, t1 = float(t[0]), float(t[-1])
    refrac = float(np.min(np.diff(t))) if n > 1 else 0.0
    zs = []
    for _ in range(n_sim):
        for _intento in range(20):
            t_sim = np.sort(rng.uniform(t0, t1, n))
            if n < 2 or np.min(np.diff(t_sim)) >= 0.5 * refrac:
                break
        g = buscar_grilla(t_sim, duracion_s, **kw)
        zs.append(g["z"] if g else 0.0)
    return np.asarray(zs)


# ---------------------------------------------------------------------------
# API principal
# ---------------------------------------------------------------------------

def _reasignar(t, T, fase, tol):
    """Vuelve a decidir que eventos caen en la grilla, con una tolerancia dada.

    Se usa despues de refinar, con una tolerancia atada al jitter MEDIDO en
    vez de a una fraccion del periodo. Sirve para soltar eventos espontaneos
    que habian coincidido con la grilla por casualidad: con T = 10 s y una
    tolerancia del 2 %, cualquier evento a menos de 200 ms cuenta como
    estimulado, y a 1.75 Hz de actividad espontanea eso pasa seguido.
    """
    return _asignar(t, T, fase, tol)


def _veredicto(T, err_T, significativo, fc, modo, tol_pct=5.0):
    """Que es el tren, en una frase, y como se clasifican sus eventos.

    `fc` es la frecuencia configurada a la que se busco (None si la busqueda
    fue libre). Devuelve (veredicto, clasificacion).
    """
    f = 1.0 / T if np.isfinite(T) and T > 0 else float("nan")
    if fc is None:
        if not significativo:
            return "no se encontro un tren periodico que se distinga del azar", "ninguna"
        return (f"tren periodico a {f:.4f} Hz, no se configuro ninguna frecuencia",
                "estimulados")
    if not significativo:
        return (f"se busco a {fc:g} Hz: no hay enganche (el estimulador no capturo, "
                f"o no se distingue del azar)"), "ninguna"
    ef = err_T / T ** 2 if np.isfinite(err_T) else float("nan")
    pct = 100.0 * (f - fc) / fc
    t_stat = (f - fc) / ef if (np.isfinite(ef) and ef > 0) else 0.0
    if abs(t_stat) < 3 or abs(pct) <= tol_pct:
        return f"enganchado a la frecuencia configurada ({fc:g} Hz)", "estimulados"
    return (f"tren periodico a {f:.4f} Hz, {pct:+.1f} % de la configurada ({fc:g} Hz): "
            f"no coincide, sus eventos quedan como espontaneos"), "ninguna"


def _un_tren(t, a, duracion_s, kw, min_eventos, min_captura, jitter_k, rescate_frac,
             resolucion_s, n_simulaciones, alfa, semilla):
    """Busca, valida y limpia UN tren sobre los instantes `t` (ordenados).

    Devuelve None si no hay ni un candidato (menos de `min_eventos`). Si hay
    candidato pero no es significativo, lo devuelve igual con su p: es el
    "intento de tren" que se reporta para que el equipo vea que se busco y que
    se encontro.
    """
    g = buscar_grilla(t, duracion_s, **kw)
    if g is None:
        return None
    z_busqueda = float(g["z"])

    # p-valor: el MISMO estadistico (el z de la busqueda) sobre datos sin
    # enganche de fase. Antes se comparaba el z final (con la tolerancia del
    # jitter, mucho mas estrecha) contra el z de busqueda del nulo: no eran
    # comparables. Desde 4 eventos (antes 6: con 4-5 el tren se aceptaba sin
    # prueba, Video_466).
    p = float("nan")
    if n_simulaciones > 0 and len(t) >= min_eventos:
        rng = np.random.default_rng(semilla)
        z0 = _z_nulo(t, duracion_s, n_simulaciones, rng, **kw)
        p = float((np.sum(z0 >= z_busqueda) + 1) / (n_simulaciones + 1))

    T, fase = _theil_sen(g["ranuras"], t[g["idx"]])
    jitter = mad(t[g["idx"]] - (fase + T * g["ranuras"]))
    res_min = resolucion_s or 0.02
    for _ in range(3):
        if not (np.isfinite(jitter) and jitter > 0):
            break
        tol2 = max(jitter_k * jitter, 2.0 * res_min)
        idx2, ran2 = _reasignar(t, T, fase, tol2)
        if len(idx2) < min_eventos:
            break
        n_ran2 = int(ran2[-1] - ran2[0]) + 1
        if len(idx2) < min_captura * n_ran2:
            break
        T2, fase2 = _theil_sen(ran2, t[idx2])
        if not (np.isfinite(T2) and T2 > 0):
            break
        sin_cambio = np.array_equal(idx2, g["idx"])
        T, fase, jitter = T2, fase2, mad(t[idx2] - (fase2 + T2 * ran2))
        g = dict(g)
        g.update({"idx": idx2, "ranuras": ran2, "tol": tol2})
        if sin_cambio:
            break

    # --- R5 (H36): tiempo Y amplitud, las dos -----------------------------
    # Un estimulado pasa a espontaneo solo si se desvia de su ranura mas de 1
    # fotograma Y su amplitud esta fuera de 0.5-2x la mediana de los DEMAS
    # estimulados. Ninguna de las dos alcanza sola: el tiempo solo expulsa
    # latidos reales de Video_466 (jitter genuino de 17 ms); la amplitud sola
    # seria clasificar por amplitud. Medido: solo lo cumple el evento de
    # 4.82 s de Video_prueba (-58 ms, 2.10 px contra 6.6-7.0 px).
    sacados = []
    if a is not None and len(g["idx"]) > min_eventos:
        for _ in range(len(g["idx"])):
            idx, ran = g["idx"], g["ranuras"]
            cand = []
            for k in range(len(idx)):
                # El desvio se mide contra el tren ajustado SIN ese evento: si
                # entra en el ajuste, un intruso en un extremo inclina la recta
                # hacia el y esconde su desvio (-58 ms -> -25 ms en Video_prueba).
                T_k, fase_k = _theil_sen(np.delete(ran, k), np.delete(t[idx], k))
                if not np.isfinite(T_k):
                    continue
                desv = float(t[idx[k]] - (fase_k + T_k * ran[k]))
                med = float(np.median(np.delete(a[idx], k)))
                fuera = not (AMP_COMPATIBLE[0] * med <= a[idx[k]] <= AMP_COMPATIBLE[1] * med)
                if abs(desv) > res_min and fuera:
                    cand.append((abs(desv), k, desv, med))
            if not cand or len(idx) - 1 < min_eventos:
                break
            _, k, desv, med = max(cand)
            sacados.append({"indice": int(idx[k]), "desvio_s": desv,
                            "amplitud": float(a[idx[k]]), "amplitud_mediana_tren": med})
            g = dict(g)
            g["idx"], g["ranuras"] = np.delete(idx, k), np.delete(ran, k)

    idx, ran = g["idx"], g["ranuras"]
    T, err_T, fase, jitter = _refinar(t[idx], ran)
    limitado = False
    if resolucion_s:
        piso = resolucion_s / np.sqrt(12.0)
        if not np.isfinite(jitter) or jitter < piso:
            jitter = piso
            n_ = np.asarray(ran, float)
            Sxx = float(np.sum((n_ - n_.mean()) ** 2))
            err_T = float(piso / np.sqrt(Sxx)) if Sxx > 0 else float("nan")
            limitado = True

    # --- R6 (H37): rescate de dudosos, solo DENTRO del tren ----------------
    # Un latido estimulado con el instante corrido mas que la tolerancia final
    # se reporta aparte como "dudoso" (ni se tira ni entra en el ajuste). Ahora
    # solo entre la primera y la ultima ranura capturada, y con amplitud
    # compatible: antes se buscaba en cualquier ranura del video y volvia a
    # traer como dudoso a la espontanea de 4.82 s, 10 s antes del tren.
    resc, ran_resc = [], []
    if np.isfinite(T) and T > 0:
        vent = rescate_frac * T
        med_a = float(np.median(a[idx])) if a is not None else None
        libres = np.setdiff1d(np.arange(len(t)), idx)
        ocupadas = set(int(x) for x in ran)
        for r in range(int(ran[0]), int(ran[-1]) + 1):
            if r in ocupadas or len(libres) == 0:
                continue
            d = np.abs(t[libres] - (fase + r * T))
            ok = d <= vent
            if med_a is not None:
                ok &= ((a[libres] >= AMP_COMPATIBLE[0] * med_a)
                       & (a[libres] <= AMP_COMPATIBLE[1] * med_a))
            if ok.any():
                j = int(np.flatnonzero(ok)[np.argmin(d[ok])])
                resc.append(int(libres[j]))
                ran_resc.append(r)
                libres = np.delete(libres, j)
    orden = np.argsort(resc)
    resc = np.asarray(resc, int)[orden]
    ran_resc = np.asarray(ran_resc, int)[orden]

    n_ranuras = int(ran[-1] - ran[0]) + 1
    return {"T_grilla": float(g["T"]), "T": T, "err_T": err_T, "fase": fase,
            "jitter": jitter, "jitter_limitado": limitado, "tol": float(g["tol"]),
            "z": z_busqueda, "p": p, "significativo": bool(np.isfinite(p) and p <= alfa)
            or (n_simulaciones == 0),
            "idx": idx, "ranuras": ran, "dudosos": resc, "ranuras_dudosos": ran_resc,
            "sacados": sacados, "n_ranuras": n_ranuras,
            "t_inicio": float(t[idx[0]]), "t_fin": float(t[idx[-1]])}


def separar(tiempos, amplitudes=None, duracion_s=None, periodo_min=0.3,
            periodo_max=None, min_eventos=4, min_captura=0.75, jitter_k=4.0,
            rescate_frac=0.10, resolucion_s=None, tol_s=None,
            n_simulaciones=N_SIMULACIONES, alfa=0.01, semilla=0,
            frecuencia_configurada_Hz=None, ventana_frac=VENTANA_DIRIGIDA,
            tol_frac=None, tol_min_s=None) -> dict:
    """
    Separa los eventos en estimulados (enganchados en fase) y espontaneos.

    DOS MODOS (Fase 3, grupo 1)
    ---------------------------
    * Con `frecuencia_configurada_Hz` (un numero, o una lista si el protocolo
      cambia de frecuencia): busqueda DIRIGIDA. Para cada frecuencia se busca
      UN tren solo entre 0.9 y 1.1 veces su periodo, sobre los eventos que
      todavia no se asignaron. La pregunta es "el estimulador capturo a las
      celulas?", y la respuesta es "enganchado a 0.1 Hz" o "no hay enganche".
    * Sin frecuencia: busqueda LIBRE de UN tren (periodos de 0.3 s a ~span/3),
      y el veredicto dice "tren periodico a X Hz, no se configuro ninguna
      frecuencia".

    Por que dirigida: el p-valor compara el tren contra listas de instantes al
    azar a las que se les corre LA MISMA busqueda (ver `_z_nulo`). Si se
    prueban todos los periodos, el azar tiene miles de intentos y arma trenes
    que puntuan casi como uno real: medido, con espontaneas a ~0.3 por segundo
    y 6 latidos estimulados, la busqueda libre no confirmaba el tren en 6 de
    20 series; la dirigida, en 0 de 20. Y en 25 series de solo espontaneas, la
    dirigida no invento ningun tren.

    Las espontaneas no se buscan como tren: se describen por la mediana, el
    rango y la frecuencia evento a evento de sus intervalos (no siguen un reloj).

    Otros cambios de la Fase 3: los `tiempos` que pasa contraction_report son
    el INICIO de cada contraccion; tolerancia de busqueda 2 fotogramas;
    Monte Carlo desde 4 eventos con 1000 simulaciones sobre el z de la
    busqueda; R5 (un estimulado sale solo si falla en tiempo Y amplitud); R6
    (dudosos solo dentro del tren y con amplitud compatible).
    `tol_frac` y `tol_min_s` se aceptan por compatibilidad y no se usan.
    """
    t = np.asarray(tiempos, float)
    orden = np.argsort(t)
    t = t[orden]
    a = np.asarray(amplitudes, float)[orden] if amplitudes is not None else None
    if duracion_s is None:
        duracion_s = float(t[-1] - t[0]) if len(t) > 1 else 0.0
    frecs = ([] if frecuencia_configurada_Hz is None
             else [float(x) for x in np.atleast_1d(frecuencia_configurada_Hz)])

    if tol_s is None:
        tol_s = (max(TOL_BUSQUEDA_FRAMES * resolucion_s, 0.05) if resolucion_s else 0.10)
    kw = dict(periodo_min=periodo_min, periodo_max=periodo_max,
              tol_s=tol_s, min_eventos=min_eventos, min_captura=min_captura)

    n = len(t)
    grupo = np.array(["espontaneos"] * n, dtype=object)
    tren_de = np.zeros(n, int)
    trenes, filas, dudosos_tab, sacados_tab = [], [], [], []
    libres = np.arange(n)
    busquedas = ([(fc, f"dirigida a {fc:g} Hz",
                   dict(kw, periodo_min=(1 - ventana_frac) / fc, periodo_max=(1 + ventana_frac) / fc))
                  for fc in frecs] if frecs else [(None, "libre", kw)])
    for k, (fc, modo, kw_k) in enumerate(busquedas, start=1):
        if len(libres) < min_eventos:
            filas.append({"tren": k, "busqueda": modo,
                          "veredicto": f"no se pudo buscar: quedan {len(libres)} eventos (< {min_eventos})",
                          "clasificacion": "ninguna"})
            continue
        tr = _un_tren(t[libres], a[libres] if a is not None else None, duracion_s, kw_k,
                      min_eventos, min_captura, jitter_k, rescate_frac, resolucion_s,
                      n_simulaciones, alfa, semilla + k - 1)
        if tr is None:
            ver = (f"se busco a {fc:g} Hz: ningun tren de {min_eventos} o mas eventos"
                   if fc else f"ningun tren de {min_eventos} o mas eventos")
            filas.append({"tren": k, "busqueda": modo, "veredicto": ver, "clasificacion": "ninguna"})
            continue
        tr["idx"] = libres[tr["idx"]]
        tr["dudosos"] = libres[tr["dudosos"]]
        for x in tr["sacados"]:
            x["indice"] = int(libres[x["indice"]])
        ver, clase = _veredicto(tr["T"], tr["err_T"], tr["significativo"], fc, modo)
        tr.update(tren=k, busqueda=modo, veredicto=ver, clasificacion=clase,
                  frecuencia_configurada_Hz=fc)
        trenes.append(tr)
        f = 1.0 / tr["T"] if np.isfinite(tr["T"]) and tr["T"] > 0 else float("nan")
        filas.append({
            "tren": k, "busqueda": modo, "veredicto": ver, "clasificacion": clase,
            "periodo_s": round(tr["T"], 5), "periodo_err_s": round(tr["err_T"], 5),
            "frecuencia_Hz": round(f, 5), "jitter_ms": round(1000 * tr["jitter"], 2),
            "z": round(tr["z"], 3), "p_valor": tr["p"],
            "n_eventos_tren": int(len(tr["idx"])), "n_ranuras": tr["n_ranuras"],
            "captura_pct": round(100 * len(tr["idx"]) / tr["n_ranuras"], 1),
            "n_dudosos": int(len(tr["dudosos"])), "n_sacados_tiempo_amplitud": len(tr["sacados"]),
            "inicio_s": round(tr["t_inicio"], 3), "fin_s": round(tr["t_fin"], 3)})
        if clase != "estimulados":
            continue
        grupo[tr["idx"]] = "estimulados"
        grupo[tr["dudosos"]] = "estimulados_dudosos"
        tren_de[tr["idx"]] = k
        tren_de[tr["dudosos"]] = k
        for i, r in zip(tr["dudosos"], tr["ranuras_dudosos"]):
            dudosos_tab.append({"tren": k, "indice_evento": int(i),
                                "tiempo_s": round(float(t[i]), 3),
                                "ranura": int(r - tr["ranuras"][0] + 1),
                                "desvio_s": round(float(t[i] - (tr["fase"] + tr["T"] * r)), 4)})
        for x in tr["sacados"]:
            sacados_tab.append({"tren": k, "indice_evento": x["indice"],
                                "tiempo_s": round(float(t[x["indice"]]), 3),
                                "desvio_s": round(x["desvio_s"], 4),
                                "amplitud": round(x["amplitud"], 4),
                                "amplitud_mediana_tren": round(x["amplitud_mediana_tren"], 4)})
        libres = np.setdiff1d(libres, np.union1d(tr["idx"], tr["dudosos"]))

    out = {"n_eventos": int(n), "fuente_tiempo": None,
           "modo_busqueda": "dirigida" if frecs else "libre",
           "trenes": pd.DataFrame(filas),
           "dudosos": pd.DataFrame(dudosos_tab),
           "sacados_tiempo_amplitud": pd.DataFrame(sacados_tab),
           "grupo_por_evento": grupo, "tren_por_evento": tren_de}
    for nombre in ("estimulados", "estimulados_dudosos", "espontaneos"):
        out[nombre] = np.flatnonzero(grupo == nombre)
    out["hay_estimulacion"] = bool(len(out["estimulados"]))
    out["n_trenes_estimulados"] = int(sum(tr["clasificacion"] == "estimulados" for tr in trenes))
    if len(out["estimulados_dudosos"]):
        out["n_estimulados_dudosos"] = int(len(out["estimulados_dudosos"]))

    # Tren PRINCIPAL (el que va al resumen y a la figura): el primero
    # estimulado; si no hay, el mejor intento, para reportarlo.
    principal = next((tr for tr in trenes if tr["clasificacion"] == "estimulados"),
                     trenes[0] if trenes else None)
    if principal is None:
        out["veredicto"] = "; ".join(f["veredicto"] for f in filas) or "sin eventos"
        out["motivo"] = out["veredicto"]
    else:
        T, err_T = principal["T"], principal["err_T"]
        out.update({
            "tren_principal": principal["tren"], "veredicto": principal["veredicto"],
            "z": round(principal["z"], 3), "p_valor": principal["p"],
            "periodo_grilla_s": round(principal["T_grilla"], 4),
            "periodo_s": round(T, 5), "periodo_err_s": round(err_T, 5),
            "frecuencia_Hz": round(1 / T, 5) if np.isfinite(T) and T > 0 else float("nan"),
            "frecuencia_err_Hz": (round(err_T / T ** 2, 6)
                                  if all(np.isfinite([T, err_T])) and T > 0 else float("nan")),
            "jitter_s": round(principal["jitter"], 5),
            "tolerancia_s": round(principal["tol"], 4),
            "n_estimulados": int(len(principal["idx"])),
            "n_ranuras": int(principal["n_ranuras"]),
            "tasa_captura_pct": round(100 * len(principal["idx"]) / principal["n_ranuras"], 1),
            "tren_inicio_s": round(principal["t_inicio"], 3),
            "tren_fin_s": round(principal["t_fin"], 3)})
        if principal["jitter_limitado"]:
            out["jitter_limitado_por_resolucion"] = True
        if not out["hay_estimulacion"]:
            out["motivo"] = (f"{principal['veredicto']} (mejor intento: T={T:.3f} s, "
                             f"z={principal['z']:.2f}, p={principal['p']:.3f})")

    # --- resumen por grupo ---------------------------------------------------
    filas_g = []
    for nombre in ("estimulados", "estimulados_dudosos", "espontaneos"):
        idx = out[nombre]
        if len(idx) == 0:
            continue
        tt = t[idx]
        iv = np.diff(tt)
        fila = {"grupo": nombre, "n": int(len(idx)),
                "t_inicio_s": round(float(tt.min()), 2), "t_fin_s": round(float(tt.max()), 2)}
        if len(iv):
            fila["intervalo_mediano_s"] = round(float(np.median(iv)), 4)
            fila["intervalo_IQR_s"] = round(float(np.percentile(iv, 75) - np.percentile(iv, 25)), 4)
            fila["frecuencia_mediana_Hz"] = round(float(1 / np.median(iv)), 4)
            fila["CV_intervalo_pct"] = round(float(100 * np.std(iv, ddof=0) / np.mean(iv)), 1)
        if a is not None:
            fila["amplitud_mediana_px"] = round(float(np.median(a[idx])), 4)
            fila["amplitud_IQR_px"] = round(
                float(np.percentile(a[idx], 75) - np.percentile(a[idx], 25)), 4)
        filas_g.append(fila)
    out["resumen_grupos"] = pd.DataFrame(filas_g)

    esp = t[out["espontaneos"]]
    if len(esp) > 1:
        iv = np.diff(esp)
        out["espontaneas_instantanea"] = pd.DataFrame({
            "tiempo_s": np.round(0.5 * (esp[1:] + esp[:-1]), 3),
            "intervalo_s": np.round(iv, 4), "frecuencia_Hz": np.round(1 / iv, 4)})
    else:
        out["espontaneas_instantanea"] = pd.DataFrame(
            columns=["tiempo_s", "intervalo_s", "frecuencia_Hz"])

    # --- grilla de cada tren: que ranura se capturo y cual se perdio ---------
    grillas = []
    for tr in trenes:
        if tr["clasificacion"] != "estimulados" and tr is not principal:
            continue
        r0, r1 = int(tr["ranuras"][0]), int(tr["ranuras"][-1])
        todas = np.arange(r0, r1 + 1)
        cap = np.isin(todas, tr["ranuras"])
        real = np.full(len(todas), np.nan)
        real[cap] = t[tr["idx"]]
        esperado = tr["fase"] + tr["T"] * todas
        grillas.append(pd.DataFrame({
            "tren": tr["tren"], "ranura": todas - r0 + 1,
            "t_esperado_s": np.round(esperado, 4), "t_medido_s": np.round(real, 4),
            "error_s": np.round(real - esperado, 5), "capturada": cap}))
    cols_g = ["tren", "ranura", "t_esperado_s", "t_medido_s", "error_s", "capturada"]
    out["grilla"] = (pd.concat(grillas, ignore_index=True) if grillas
                     else pd.DataFrame(columns=cols_g))
    return out


def comparar_con_equipo(res: dict, frecuencia_configurada_Hz: float,
                        fps_nominal: float | None = None,
                        tol_pct: float = 5.0) -> dict:
    """Contrasta la frecuencia medida contra la configurada en el estimulador.

    Devuelve la diferencia en Hz, en % y en unidades del error estandar.

    OJO CON UNA DIFERENCIA CHICA PERO SIGNIFICATIVA. El estimulador es un
    reloj de cuarzo: su frecuencia es mucho mas confiable que el `fps` que
    declara el archivo de video, que suele venir redondeado o directamente
    mal. Como TODOS los tiempos del analisis salen de dividir el numero de
    fotograma por ese fps, un fps equivocado escala toda la base de tiempo y
    aparece como un desvio sistematico del mismo signo en cada video.

    Por eso, si la diferencia es significativa pero menor que `tol_pct`, lo
    mas probable no es que falle el equipo sino la base de tiempo del video, y
    esta funcion devuelve el `fps` corregido. Usar el estimulador para
    calibrar el fps es legitimo y de hecho es el patron mas preciso que hay a
    mano en el montaje.
    """
    if not res.get("hay_estimulacion"):
        return {"comparable": False,
                "motivo": "no se detecto un tren estimulado en este video"}
    f, ef = res["frecuencia_Hz"], res["frecuencia_err_Hz"]
    d = f - frecuencia_configurada_Hz
    pct = 100 * d / frecuencia_configurada_Hz
    t_stat = (d / ef) if (np.isfinite(ef) and ef > 0) else float("nan")

    out = {
        "comparable": True,
        "frecuencia_configurada_Hz": frecuencia_configurada_Hz,
        "frecuencia_medida_Hz": f,
        "error_estandar_Hz": ef,
        "diferencia_Hz": round(d, 6),
        "diferencia_pct": round(pct, 3),
        "t": round(t_stat, 2) if np.isfinite(t_stat) else float("nan"),
    }

    if not np.isfinite(t_stat) or abs(t_stat) < 3:
        out["veredicto"] = "indistinguible de lo configurado"
    elif abs(pct) <= tol_pct:
        out["veredicto"] = (f"desvio sistematico de {pct:+.2f} %. Es chico y muy significativo: "
                            f"lo mas probable es que el fps del video este mal, no el equipo")
        if fps_nominal:
            out["fps_declarado"] = fps_nominal
            # fps_real = fotogramas_por_periodo / periodo_verdadero, y
            # fotogramas_por_periodo = T_medido * fps_declarado. O sea que el
            # factor DIVIDE, no multiplica: si la frecuencia medida salio baja,
            # es porque el video corre mas rapido de lo que declara.
            out["fps_corregido"] = round(fps_nominal / (1 + pct / 100), 4)
            out["fotogramas_por_periodo"] = round(res["periodo_s"] * fps_nominal, 2)
            out["nota_fps"] = ("Reprocesar con este fps alinea toda la base de tiempo. "
                               "Verificarlo con un segundo video estimulado a otra "
                               "frecuencia: si el factor de correccion es el mismo, es el fps.")
    else:
        out["veredicto"] = (f"difiere {pct:+.1f} % de lo configurado, demasiado para ser la base "
                            f"de tiempo: revisar el equipo o la deteccion de eventos")
    return out
