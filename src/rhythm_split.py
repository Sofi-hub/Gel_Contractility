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
1. Se barre un rango de periodos candidatos T.
2. Para cada T se prueba, como origen de fase, el instante de cada evento (el
   optimo siempre se puede anclar en un evento) y se cuenta cuantas RANURAS de
   la grilla quedan ocupadas por algun evento dentro de una tolerancia.
3. Se puntua con un z-score contra lo que daria el azar:

       z = (ranuras_ocupadas - esperado) / sqrt(varianza)

   con el esperado calculado a partir de la densidad de eventos en la ventana.
   Este z penaliza solo los dos modos de fallar: un T muy grande deja pocas
   ranuras (z baja aunque todas se llenen) y un armonico T/2 deja la mitad de
   las ranuras vacias (z baja tambien). Por eso el T verdadero gana.
4. El T ganador se refina por minimos cuadrados sobre los eventos asignados
   (regresion de t contra el numero de ranura), lo que da T con error estandar.

VALIDACION ESTADISTICA
-----------------------
Todas las elecciones anteriores son post-hoc: se eligio el T que mejor puntua,
y la ventana donde el tren existe. Para que el resultado signifique algo, el
p-valor se calcula por Monte Carlo corriendo EL MISMO procedimiento completo
sobre datos barajados (se permutan los intervalos entre eventos, lo que
conserva la distribucion de intervalos pero destruye el enganche de fase). El
p-valor sale de comparar el z observado contra la distribucion del z MAXIMO de
las simulaciones, asi que ya tiene en cuenta que se probaron muchos periodos.

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

    periodos = np.geomspace(periodo_min, periodo_max, n_candidatos)
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

    validos = []
    for k in cand:
        T, tol = float(periodos[k]), float(tols[k])
        idx, ranuras = _asignar(t, T, t[anclas[k]], tol)
        if len(idx) < min_eventos:
            continue
        t_ini, t_fin = t[idx[0]], t[idx[-1]]
        n_ranuras = int(ranuras[-1] - ranuras[0]) + 1
        if len(idx) < min_captura * n_ranuras:     # primer filtro anti-armonico
            continue
        dur = max(t_fin - t_ini, 1e-9)
        en_ventana = int(np.sum((t >= t_ini) & (t <= t_fin)))
        z = _z_periodicidad(len(idx), n_ranuras, en_ventana / dur, tol)
        validos.append({"T": T, "fase": float(t[anclas[k]]), "tol": tol, "z": z,
                        "idx": idx, "ranuras": ranuras,
                        "n_ocupadas": len(idx), "n_ranuras": n_ranuras,
                        "t_inicio": float(t_ini), "t_fin": float(t_fin)})
    if not validos:
        return None

    # SEGUNDO filtro anti-armonico, y el que hace el trabajo pesado: entre los
    # candidatos que puntuan casi tan bien como el mejor, quedarse con el
    # periodo MAS LARGO. Un armonico de un periodo verdadero T siempre esta en
    # T/2, T/3, ... o sea siempre es MENOR. El subarmonico 2T, que si seria
    # mayor, usa la mitad de los eventos y normalmente no llega a min_eventos.
    z_max = max(v["z"] for v in validos)
    cerca = [v for v in validos if v["z"] >= 0.90 * z_max]
    return max(cerca, key=lambda v: v["T"])
    return mejor


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
    jitter = (float(np.median(np.abs(resid - np.median(resid))) * 1.4826)
              if len(resid) > 1 else float("nan"))
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


def separar(tiempos, amplitudes=None, duracion_s=None, periodo_min=0.3,
            periodo_max=None, tol_frac=0.02, tol_min_s=0.05, min_eventos=4,
            min_captura=0.75, jitter_k=4.0, rescate_frac=0.10, resolucion_s=None,
            tol_s=None,
            n_simulaciones=200, alfa=0.01, semilla=0) -> dict:
    """
    Separa los eventos en estimulados (enganchados en fase) y espontaneos.

    Parameters
    ----------
    tiempos : instantes de los eventos, en segundos.
    amplitudes : opcional. NO se usa para clasificar: se reporta por grupo
        como verificacion independiente. Si los dos grupos resultan tener
        amplitudes distintas sin que la amplitud haya intervenido en la
        clasificacion, eso es evidencia a favor de que la separacion es real.
    duracion_s : duracion del registro. Por defecto, el span de los eventos.
    periodo_min / periodo_max : rango de periodos a buscar (s).
    tol_frac / tol_min_s : tolerancia de coincidencia con la grilla, como
        fraccion del periodo y como piso absoluto.
    min_eventos : minimo de coincidencias para considerar que hay un tren.
    n_simulaciones : repeticiones del Monte Carlo. 0 lo desactiva.
    alfa : nivel al que se exige el p-valor para declarar que hay estimulacion.
    """
    t = np.asarray(tiempos, float)
    orden = np.argsort(t)
    t = t[orden]
    a = np.asarray(amplitudes, float)[orden] if amplitudes is not None else None
    if duracion_s is None:
        duracion_s = float(t[-1] - t[0]) if len(t) > 1 else 0.0

    # Por defecto la tolerancia es de 3 fotogramas: por debajo de eso no se
    # puede medir el instante de un evento, asi que exigir mas seria exigir
    # precision que la camara no da.
    if tol_s is None:
        tol_s = max(3.0 * resolucion_s, 0.05) if resolucion_s else 0.10
    kw = dict(periodo_min=periodo_min, periodo_max=periodo_max,
              tol_s=tol_s, min_eventos=min_eventos, min_captura=min_captura)

    out = {"n_eventos": int(len(t)), "hay_estimulacion": False,
           "estimulados": np.array([], int), "espontaneos": np.arange(len(t))}

    g = buscar_grilla(t, duracion_s, **kw)
    if g is None:
        out["motivo"] = f"menos de {min_eventos} eventos, o rango de periodos vacio"
        return out

    # Primero un ajuste ROBUSTO, para que un espontaneo colado en un extremo
    # del tren no incline la recta y se esconda (ver _theil_sen).
    T, fase = _theil_sen(g["ranuras"], t[g["idx"]])
    resid = t[g["idx"]] - (fase + T * g["ranuras"])
    jitter = float(np.median(np.abs(resid - np.median(resid))) * 1.4826)
    err_T = float("nan")

    # Segunda pasada: reasignar con una tolerancia atada al jitter medido, no
    # a una fraccion del periodo, y volver a refinar. Esto suelta espontaneas
    # que habian coincidido con la grilla por casualidad.
    for _ in range(3):
        if not (np.isfinite(jitter) and jitter > 0):
            break
        tol2 = max(jitter_k * jitter, 2.0 * (resolucion_s or 0.02))
        idx2, ran2 = _reasignar(t, T, fase, tol2)
        if len(idx2) < min_eventos:
            break
        n_ran2 = int(ran2[-1] - ran2[0]) + 1
        if len(idx2) < min_captura * n_ran2:
            break
        T2, fase2 = _theil_sen(ran2, t[idx2])
        if not (np.isfinite(T2) and T2 > 0):
            break
        r2 = t[idx2] - (fase2 + T2 * ran2)
        jit2 = float(np.median(np.abs(r2 - np.median(r2))) * 1.4826)
        sin_cambio = (len(idx2) == len(g["idx"]) and np.array_equal(idx2, g["idx"]))
        T, fase, jitter = T2, fase2, jit2
        g = dict(g)
        g.update({"idx": idx2, "ranuras": ran2, "tol": tol2,
                  "n_ocupadas": len(idx2), "n_ranuras": n_ran2,
                  "t_inicio": float(t[idx2[0]]), "t_fin": float(t[idx2[-1]])})
        if sin_cambio:
            break
    # z recalculado con la tolerancia final, que es mucho mas exigente que la
    # del barrido: con una ventana de +-4 jitter en vez de +-2 % del periodo,
    # la probabilidad de coincidir por azar cae y el z sube donde hay senal.
    # Ajuste final por minimos cuadrados sobre el conjunto ya limpio: ahi si
    # es el estimador correcto, y es el que da el error estandar del periodo.
    T, err_T, fase, jitter = _refinar(t[g["idx"]], g["ranuras"])

    # La incertidumbre no puede ser menor que la resolucion con la que se
    # midieron los instantes. En estos videos el tren estimulado cae SIEMPRE en
    # el mismo numero de fotogramas, asi que los residuos dan exactamente cero
    # y el ajuste reporta error cero, que es falso: lo que pasa es que el
    # jitter real esta por debajo de un fotograma. Se pone como piso el error
    # de cuantizacion, resolucion/sqrt(12).
    if resolucion_s:
        piso = resolucion_s / np.sqrt(12.0)
        if not np.isfinite(jitter) or jitter < piso:
            jitter = piso
            n_ = np.asarray(g["ranuras"], float)
            Sxx = float(np.sum((n_ - n_.mean()) ** 2))
            err_T = float(piso / np.sqrt(Sxx)) if Sxx > 0 else float("nan")
            out["jitter_limitado_por_resolucion"] = True

    _dur = max(g["t_fin"] - g["t_inicio"], 1e-9)
    _en_v = int(np.sum((t >= g["t_inicio"]) & (t <= g["t_fin"])))
    g["z"] = _z_periodicidad(g["n_ocupadas"], g["n_ranuras"], _en_v / _dur, g["tol"])

    p = float("nan")
    if n_simulaciones > 0 and len(t) >= min_eventos + 2:
        rng = np.random.default_rng(semilla)
        z0 = _z_nulo(t, duracion_s, n_simulaciones, rng, **kw)
        # (+1)/(+1): estimador conservador del p-valor con simulaciones finitas
        p = float((np.sum(z0 >= g["z"]) + 1) / (n_simulaciones + 1))

    out.update({
        "z": round(g["z"], 3), "p_valor": p,
        "periodo_grilla_s": round(g["T"], 4),
        "periodo_s": round(T, 5), "periodo_err_s": round(err_T, 5),
        "frecuencia_Hz": round(1 / T, 5) if T and np.isfinite(T) and T > 0 else float("nan"),
        "frecuencia_err_Hz": (round(err_T / T ** 2, 6)
                              if all(np.isfinite([T, err_T])) and T > 0 else float("nan")),
        "jitter_s": round(jitter, 5),
        "tolerancia_s": round(g["tol"], 4),
        "n_estimulados": int(g["n_ocupadas"]),
        "n_ranuras": int(g["n_ranuras"]),
        "tasa_captura_pct": round(100 * g["n_ocupadas"] / g["n_ranuras"], 1),
        "tren_inicio_s": round(g["t_inicio"], 3),
        "tren_fin_s": round(g["t_fin"], 3),
    })

    # --- rescate de latidos con tiempo anomalo ------------------------------
    # La tolerancia final es muy estrecha (unos pocos fotogramas). Un latido
    # estimulado cuyo instante detectado se corrio mas que eso caeria en
    # "espontaneo", que es la clasificacion mas enganosa posible: un evento
    # claramente parte del tren, escondido entre las espontaneas. Medido en
    # Video_063: el 5o latido aparece 0.33 s antes de su ranura y se perdia.
    # Se lo busca en una ventana mas ancha y se lo reporta APARTE, como dudoso:
    # ni se lo tira ni se lo mezcla con los buenos, y no entra en el ajuste del
    # periodo para no contaminarlo.
    rescatados, ranuras_resc = [], []
    if np.isfinite(T) and T > 0:
        vent = rescate_frac * T
        libres = np.setdiff1d(np.arange(len(t)), g["idx"])
        r_lo = int(np.floor((t[0] - fase) / T))
        r_hi = int(np.ceil((t[-1] - fase) / T))
        ocupadas = set(int(x) for x in g["ranuras"])
        for r in range(r_lo, r_hi + 1):
            if r in ocupadas or len(libres) == 0:
                continue
            centro = fase + r * T
            d = np.abs(t[libres] - centro)
            j = int(np.argmin(d))
            if d[j] <= vent:
                rescatados.append(int(libres[j]))
                ranuras_resc.append(r)
                libres = np.delete(libres, j)
    rescatados = np.array(sorted(rescatados), dtype=int)

    significativo = (not np.isfinite(p)) or (p <= alfa)
    if significativo:
        out["hay_estimulacion"] = True
        out["estimulados"] = g["idx"]
        out["estimulados_dudosos"] = rescatados
        out["espontaneos"] = np.setdiff1d(np.arange(len(t)),
                                          np.union1d(g["idx"], rescatados))
        if len(rescatados):
            out["n_estimulados_dudosos"] = int(len(rescatados))
            out["dudosos"] = pd.DataFrame({
                "indice_evento": rescatados,
                "tiempo_s": np.round(t[rescatados], 3),
                "ranura": np.array(ranuras_resc, dtype=int) - int(g["ranuras"][0]) + 1,
                "desvio_s": np.round(t[rescatados] - (fase + T * np.array(ranuras_resc)), 4),
            })
    else:
        out["motivo"] = (f"el mejor tren periodico (T={g['T']:.3f}s, z={g['z']:.2f}) "
                         f"no supera lo que da el azar (p={p:.3f})")

    # --- resumen por grupo ---------------------------------------------------
    grupos = []
    for nombre, idx in (("estimulados", out["estimulados"]),
                        ("estimulados_dudosos", out.get("estimulados_dudosos", np.array([], int))),
                        ("espontaneos", out["espontaneos"])):
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
        grupos.append(fila)
    out["resumen_grupos"] = pd.DataFrame(grupos)

    # --- frecuencia instantanea de las espontaneas ---------------------------
    # No se resume en un numero: estas celulas no mantienen una frecuencia
    # constante, asi que lo informativo es como deriva a lo largo del registro.
    esp = t[out["espontaneos"]]
    if len(esp) > 1:
        iv = np.diff(esp)
        out["espontaneas_instantanea"] = pd.DataFrame({
            "tiempo_s": np.round(0.5 * (esp[1:] + esp[:-1]), 3),
            "intervalo_s": np.round(iv, 4),
            "frecuencia_Hz": np.round(1 / iv, 4),
        })
    else:
        out["espontaneas_instantanea"] = pd.DataFrame(
            columns=["tiempo_s", "intervalo_s", "frecuencia_Hz"])

    # --- tabla de la grilla: que ranura se capturo y cual se perdio -----------
    if out["hay_estimulacion"]:
        r0, r1 = int(g["ranuras"][0]), int(g["ranuras"][-1])
        todas = np.arange(r0, r1 + 1)
        esperado = fase + T * todas
        capturada = np.isin(todas, g["ranuras"])
        real = np.full(len(todas), np.nan)
        real[capturada] = t[g["idx"]]
        out["grilla"] = pd.DataFrame({
            "ranura": todas - r0 + 1,
            "t_esperado_s": np.round(esperado, 4),
            "t_medido_s": np.round(real, 4),
            "error_s": np.round(real - esperado, 5),
            "capturada": capturada,
        })
    else:
        out["grilla"] = pd.DataFrame(
            columns=["ranura", "t_esperado_s", "t_medido_s", "error_s", "capturada"])

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
