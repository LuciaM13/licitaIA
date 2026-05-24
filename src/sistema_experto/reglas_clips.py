"""
Base de conocimiento del sistema experto (CLIPS).

Único núcleo CLIPS del sistema. Describe el comportamiento del experto sobre
los parámetros del proyecto emitiendo **alertas** al licitador cuando ciertas
combinaciones de parámetros requieren atención. La mayoría de reglas evalúan
directamente los slots de ``datos-proyecto`` y asserta un hecho ``alerta``,
sin etiquetas intermedias.

Existe **una regla de orden superior** (``alerta-meta-proyecto-alto-riesgo``)
que NO mira ``datos-proyecto``: solo lee otras alertas ya emitidas y deriva
una alerta agregada. Esto reintroduce el encadenamiento real (forward
chaining sobre hechos ``alerta``) sin recurrir a etiquetas intermedias.

Las decisiones de elegibilidad de materiales viven en ``src/domain/reglas/elegibilidad.py``
(Python puro, sin inferencia). Este módulo se ocupa solo de la parte IA real.

Vocabulario:
  - ``nivel`` (error|warning|info) = urgencia de la alerta para el licitador
    (icono de la alerta en UI).

Convención de fuentes: el slot ``fuente`` de cada alerta guarda la cita
documental ("Excel EMASESA", "RD 396/2006", "regla interna", "provisional")
para trazabilidad y tooltip. El cuerpo del ``msg`` de cada alerta NO debe
contener citas normativas — el texto visible se mantiene corto y en lenguaje
llano.
"""

# Re-export para compatibilidad: el valor canónico vive en src.modelo.constantes.
from src.modelo.constantes import NULL_SENTINEL  # noqa: E402, F401


# ---------------------------------------------------------------------------
# Umbrales del sistema experto
# ---------------------------------------------------------------------------
# Se extraen a un dict Python para no hardcodearlos en la base CLIPS. Se
# inyectan vía f-string al construir las reglas. Cualquier cambio de política
# (revisión con técnico EMASESA, ajuste tras campaña, etc.) se hace aquí sin
# tocar reglas. Marcados con ``fuente=provisional`` los umbrales que aún no
# tienen respaldo documental.

UMBRALES: dict[str, float] = {
    # Zanja compleja: profundidad ABA o SAN que separa obra estándar de compleja.
    # Provisional — pdte validación con técnico EMASESA. NTE-ADZ marca cambio
    # de tipología de entibación en ese rango, pero no es umbral oficial EMASESA.
    "zanja_compleja_prof_m": 3.5,

    # Tramo urbano denso: combinación de longitud ABA y nº de acometidas.
    "tramo_urbano_longitud_m": 100.0,
    "tramo_urbano_acometidas_min": 5,

    # Zanja compartida probable: diferencia máxima entre profundidad ABA y SAN.
    "zanja_compartida_delta_m": 0.3,

    # Seguridad y Salud: umbrales de alerta sobre pct_seguridad (fracción 0-1).
    # < 0.02 → crítico (error). 0.02 ≤ S&S < 0.03 → margen bajo en obra compleja.
    "ss_critico_pct": 0.02,
    "ss_bajo_obra_compleja_pct": 0.03,

    # ABA larga sin acometidas.
    "aba_larga_longitud_m": 200.0,

    # Valvulería aproximada: la BD agrupa por rango DN mientras el Excel
    # EMASESA define precio por DN puntual. Por encima de este DN la
    # estimación tiene sesgo detectable (audit A2C 2026-04-19).
    "valvuleria_aprox_dn_mm": 300,

    # Profundidad ABA fuera del rango habitual (catalogo EMASESA).
    # Mínimo respaldado por carga de tráfico (Said 2024); máximo por
    # cambio de régimen geotécnico (Ma 2024).
    "prof_aba_min_m": 0.6,
    "prof_aba_max_m": 6.0,

    # Profundidad SAN fuera del rango habitual.
    "prof_san_min_m": 1.0,
    "prof_san_max_m": 6.0,

    # Saneamiento profundo: cambio cualitativo de régimen geotécnico
    # (Chaloulos 2015, Qin 2022). Umbral operativo, no físico.
    "saneamiento_profundo_m": 4.0,

    # Zanja somera: cubierta < 1.0 m amplifica carga de tráfico (Said 2024).
    "zanja_somera_m": 1.0,

    # FD de gran diámetro requiere anclajes en codos y derivaciones en T (Chen 2023).
    "fd_dn_min_mm": 400,

    # PE de pequeño diámetro: confirmar presión nominal (Bouaziz 2018).
    "pe_dn_max_mm": 90,

    # Densidad de acometidas anómala según corpus EMASESA (max real 0.16).
    "densidad_acom_max": 0.30,

    # Rango habitual del % S&S (Shohet 2018, Bachar 2024 — óptimo 0.67-3.8 %;
    # corpus EMASESA real 2.78-7.36 %).
    "pct_seg_min": 0.01,
    "pct_seg_max": 0.10,

    # Rango habitual del % Gestión Ambiental EMASESA (mediana 7.81 %, max 10.13 %
    # en los 7 proyectos; agrega Gestión Residuos + Protección Arbolado).
    "pct_gest_min": 0.005,
    "pct_gest_max": 0.11,

    # Margen mínimo de S&S en obras con amianto (heurística operativa
    # EMASESA + RD 396/2006).
    "pct_seg_amianto_min": 0.04,
}


# ---------------------------------------------------------------------------
# Templates (esquema de hechos del sistema experto)
# ---------------------------------------------------------------------------

TEMPLATES = """
(deftemplate datos-proyecto
  (slot aba_activa              (type INTEGER))
  (slot san_activa              (type INTEGER))
  (slot aba_longitud_m          (type FLOAT))
  (slot aba_profundidad_m       (type FLOAT))
  (slot san_profundidad_m       (type FLOAT))
  (slot aba_diametro_mm         (type INTEGER))
  (slot san_diametro_mm         (type INTEGER))
  (slot aba_tipo_tuberia        (type STRING))
  (slot acometidas_aba_n        (type INTEGER))
  (slot acometidas_san_n        (type INTEGER))
  (slot desmontaje_tipo         (type STRING))
  (slot pct_seguridad           (type FLOAT))
  (slot pct_gestion             (type FLOAT))
  (slot conduccion_provisional_m (type FLOAT))
  (slot pozos_existentes_aba    (type STRING))
  (slot pozos_existentes_san    (type STRING))
  (slot instalacion_valvuleria  (type STRING)))

(deftemplate alerta
  (slot nivel   (type STRING))
  (slot msg     (type STRING))
  (slot rule_id (type STRING))
  (slot fuente  (type STRING)))
"""


# ---------------------------------------------------------------------------
# Reglas del sistema experto
# ---------------------------------------------------------------------------
# Los umbrales se inyectan vía f-string al construir este bloque. Las reglas
# en sí hacen match contra constantes numéricas ya resueltas.

RULES = f"""
; ╔══════════════════════════════════════════════════════════════════════════╗
; ║  REGLAS DE ALERTA AL LICITADOR                                          ║
; ╚══════════════════════════════════════════════════════════════════════════╝

; ── Fibrocemento sin gestión ambiental ─────────────────────────────────────
(defrule alerta-fibrocemento-sin-gestion
  (datos-proyecto (desmontaje_tipo "fibrocemento")
                  (pct_gestion ?g&:(= ?g 0.0)))
  =>
  (assert (alerta (nivel "error")
                  (msg "Hay fibrocemento pero la Gestion Ambiental esta al 0%. Revisa ese porcentaje.")
                  (rule_id "alerta-fibrocemento-sin-gestion")
                  (fuente "RD 396/2006"))))

; ── Seguridad crítica en obra compleja ─────────────────────────────────────
(defrule alerta-seguridad-critica
  (datos-proyecto (aba_profundidad_m ?pa) (san_profundidad_m ?ps)
                  (pct_seguridad ?s&:(< ?s {UMBRALES['ss_critico_pct']})))
  (test (> (max ?pa ?ps) {UMBRALES['zanja_compleja_prof_m']}))
  =>
  (assert (alerta (nivel "error")
                  (msg "Obra profunda con la partida de Seguridad muy baja. Revisala antes de licitar.")
                  (rule_id "alerta-seguridad-critica")
                  (fuente "Excel EMASESA"))))

; ── Blindaje recomendado ───────────────────────────────────────────────────
(defrule alerta-blindaje-necesario
  (datos-proyecto (aba_profundidad_m ?pa) (san_profundidad_m ?ps)
                  (pct_seguridad ?s&:(>= ?s {UMBRALES['ss_critico_pct']})
                                  &:(< ?s {UMBRALES['ss_bajo_obra_compleja_pct']})))
  (test (> (max ?pa ?ps) {UMBRALES['zanja_compleja_prof_m']}))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Obra compleja con poco margen de Seguridad. Revisa el blindaje.")
                  (rule_id "alerta-blindaje-necesario")
                  (fuente "Excel EMASESA"))))

; ── ABA larga sin acometidas ───────────────────────────────────────────────
(defrule alerta-aba-larga-sin-acometidas
  (datos-proyecto (aba_activa 1)
                  (aba_longitud_m ?l&:(> ?l {UMBRALES['aba_larga_longitud_m']}))
                  (acometidas_aba_n ?n&:(= ?n 0)))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Red ABA larga sin acometidas. ¿Has comprobado si existen?")
                  (rule_id "alerta-aba-larga-sin-acometidas")
                  (fuente "regla interna"))))

; ── Entibación duplicada (zanja compartida) ───────────────────────────────
(defrule alerta-entibacion-doble
  (datos-proyecto (aba_activa 1) (san_activa 1)
                  (aba_profundidad_m ?pa) (san_profundidad_m ?ps))
  (test (< (abs (- ?pa ?ps)) {UMBRALES['zanja_compartida_delta_m']}))
  =>
  (assert (alerta (nivel "warning")
                  (msg "ABA y SAN a la misma profundidad. ¿Entibacion por duplicado?")
                  (rule_id "alerta-entibacion-doble")
                  (fuente "regla interna"))))

; ── Valvulería aproximada para DN grandes ─────────────────────────────────
; La BD agrupa valvulería de compuerta por rango DN, pero EMASESA publica
; precios por DN puntual con sesgo detectable a partir de DN>300 mm. Alerta
; informativa para que el licitador contraste con proyecto definitivo.
(defrule alerta-valvuleria-aproximada
  (datos-proyecto (aba_activa 1)
                  (aba_diametro_mm ?d&:(> ?d {UMBRALES['valvuleria_aprox_dn_mm']}))
                  (instalacion_valvuleria "enterrada"))
  =>
  (assert (alerta (nivel "info")
                  (msg "Valvuleria estimada para DN grande. Confirma con proyecto definitivo.")
                  (rule_id "alerta-valvuleria-aproximada")
                  (fuente "audit BD-Excel A2C 2026-04-19"))))

; ── Profundidad ABA fuera del rango habitual ──────────────────────────────
(defrule alerta-prof-aba-fuera-rango-catalogo
  (datos-proyecto (aba_activa 1) (aba_profundidad_m ?p))
  (test (or (< ?p {UMBRALES['prof_aba_min_m']})
            (> ?p {UMBRALES['prof_aba_max_m']})))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Profundidad ABA fuera del rango habitual. La estimacion puede no ser fiable.")
                  (rule_id "prof-aba-fuera-rango-catalogo")
                  (fuente "Said 2024 / Aschilean 2018"))))

; ── Profundidad SAN fuera del rango habitual ──────────────────────────────
(defrule alerta-prof-san-fuera-rango-catalogo
  (datos-proyecto (san_activa 1) (san_profundidad_m ?p))
  (test (or (< ?p {UMBRALES['prof_san_min_m']})
            (> ?p {UMBRALES['prof_san_max_m']})))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Profundidad SAN fuera del rango habitual. Revisa el rango del catalogo.")
                  (rule_id "prof-san-fuera-rango-catalogo")
                  (fuente "Ma 2024 / catalogo EMASESA"))))

; ── Pozos profundos sin escala ────────────────────────────────────────────
(defrule alerta-pozos-profundos-sin-escala
  (datos-proyecto (san_activa 1)
                  (san_profundidad_m ?ps&:(> ?ps {UMBRALES['saneamiento_profundo_m']}))
                  (pozos_existentes_san ?pozs&:(neq ?pozs "none")))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Saneamiento profundo con pozos existentes. ¿Has previsto pates y ventilacion?")
                  (rule_id "alerta-pozos-profundos-sin-escala")
                  (fuente "Ryoo 2023 / Smith 2014 (confined space)"))))

; ── FD de gran diámetro: empuje en codos y derivaciones en T ─────────────
(defrule alerta-fd-dn-grande-empuje
  (datos-proyecto (aba_tipo_tuberia "FD")
                  (aba_diametro_mm ?d&:(>= ?d {UMBRALES['fd_dn_min_mm']})))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Tuberia FD de gran diametro. ¿Has previsto anclajes en codos y derivaciones en T?")
                  (rule_id "alerta-fd-dn-grande-empuje")
                  (fuente "Chen 2023 / Rajah 2021"))))

; ── PE de pequeño DN: confirmar presión nominal ───────────────────────────
; clipspy 1.0.6 no tiene startswith confiable; enumeramos PE-100 y PE-80.
(defrule alerta-pe-dn-pequeno-presion
  (datos-proyecto (aba_tipo_tuberia ?t)
                  (aba_diametro_mm ?d&:(<= ?d {UMBRALES['pe_dn_max_mm']}))
                  (pct_seguridad ?s&:(> ?s 0.0)))
  (test (or (eq ?t "PE-100") (eq ?t "PE-80")))
  =>
  (assert (alerta (nivel "info")
                  (msg "PE pequeno: confirma la presion nominal con el pliego.")
                  (rule_id "alerta-pe-dn-pequeno-presion")
                  (fuente "Bouaziz 2018 / Gaidi 2024"))))

; ── Densidad de acometidas ABA anómala ────────────────────────────────────
; Mide densidad sobre la red ABA: acometidas ABA / longitud ABA. La regla
; antigua sumaba acometidas SAN al numerador pero dividía entre longitud
; ABA, lo que inflaba el ratio en ABA+SAN. Como el deftemplate no tiene
; san_longitud_m, la densidad SAN no se puede evaluar aquí sin sesgo.
; Requiere ABA activa y longitud > 0: con la colapsación del motor, ABA
; inactiva ya no entra; con ABA activa pero longitud aún 0 (sin item de
; tubería elegido), tampoco tiene sentido calcular.
(defrule alerta-densidad-acometidas-anomala
  (datos-proyecto (aba_activa 1)
                  (aba_longitud_m ?l&:(> ?l 0.0))
                  (acometidas_aba_n ?na))
  (test (> (/ ?na ?l) {UMBRALES['densidad_acom_max']}))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Densidad de acometidas inusual. Revisa que no haya error de captura.")
                  (rule_id "alerta-densidad-acometidas-anomala")
                  (fuente "EMASESA real (corpus 7 proyectos: max ratio 0.16)"))))

; ── Tramo urbano denso sin conducción provisional ─────────────────────────
(defrule alerta-trafico-sin-conduccion-provisional
  (datos-proyecto (aba_activa 1)
                  (aba_longitud_m ?l&:(> ?l {UMBRALES['tramo_urbano_longitud_m']}))
                  (acometidas_aba_n ?n&:(> ?n {UMBRALES['tramo_urbano_acometidas_min']}))
                  (conduccion_provisional_m ?cp&:(= ?cp 0.0)))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Tramo urbano denso sin conduccion provisional.")
                  (rule_id "alerta-trafico-sin-conduccion-provisional")
                  (fuente "Tanoli 2019 / Wu 2021"))))

; ── % Seguridad fuera del rango habitual ──────────────────────────────────
; Solapa intencionadamente con alerta-seguridad-critica (< 0.02): un proyecto
; con S&S muy bajo ve dos alertas (la genérica + la específica de obra
; compleja), lo cual es informativo, no contradictorio.
(defrule alerta-pct-seguridad-rango-anomalo
  (datos-proyecto (pct_seguridad ?s&:(> ?s 0.0)))
  (test (or (< ?s {UMBRALES['pct_seg_min']})
            (> ?s {UMBRALES['pct_seg_max']})))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Porcentaje de Seguridad fuera del rango habitual (1-10%).")
                  (rule_id "alerta-pct-seguridad-rango-anomalo")
                  (fuente "Shohet 2018 / Bachar 2024"))))

; ── % Gestión Ambiental fuera del rango habitual EMASESA ──────────────────
(defrule alerta-pct-gestion-rango-anomalo
  (datos-proyecto (pct_gestion ?g&:(> ?g 0.0)))
  (test (or (< ?g {UMBRALES['pct_gest_min']})
            (> ?g {UMBRALES['pct_gest_max']})))
  =>
  (assert (alerta (nivel "info")
                  (msg "Porcentaje de Gestion Ambiental fuera del rango habitual EMASESA.")
                  (rule_id "alerta-pct-gestion-rango-anomalo")
                  (fuente "EMASESA real (mediana 7.81%, max 10.13%)"))))

; ── Amianto con margen de Seguridad ajustado ──────────────────────────────
(defrule alerta-amianto-sin-margen-seguridad
  (datos-proyecto (desmontaje_tipo "fibrocemento")
                  (pct_seguridad ?s&:(> ?s 0.0)
                                  &:(< ?s {UMBRALES['pct_seg_amianto_min']})))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Obra con amianto: el margen de Seguridad es muy ajustado.")
                  (rule_id "alerta-amianto-sin-margen-seguridad")
                  (fuente "RD 396/2006 + Gottesfeld 2023 (heuristica operativa)"))))

; ── Alerta meta: proyecto de alto riesgo ──────────────────────────────────
; ENCADENAMIENTO REAL: esta regla NO mira `datos-proyecto`. Solo lee otras
; alertas ya emitidas y deriva una alerta agregada de orden superior.
;
; Tres subconjuntos cohesivos, cada uno con su predicado compartido:
;
;   ?r1  Riesgo geometrico de la zanja (OBLIGATORIO)
;        Predicado compartido: max(prof_aba, prof_san) > 3.5 m
;          - alerta-seguridad-critica       (S&S < 2 %)
;          - alerta-blindaje-necesario      (2 % <= S&S < 3 %)
;        Las dos son mutuamente excluyentes por bandas de pct_seguridad.
;
;   ?r2  Riesgo de contexto urbano denso (ALTERNATIVO)
;        Predicado compartido: aba_longitud_m > 100 AND acometidas_aba_n > 5
;          - alerta-trafico-sin-conduccion-provisional (sin conduccion prov.)
;
;   ?r3  Riesgo de material peligroso - amianto (ALTERNATIVO)
;        Predicado compartido: desmontaje_tipo = "fibrocemento"
;          - alerta-fibrocemento-sin-gestion    (Gestion Ambiental = 0 %)
;          - alerta-amianto-sin-margen-seguridad (S&S < 4 %)
;
; Logica de disparo: ?r1 AND (?r2 OR ?r3)
; Implementacion: como ?r2 y ?r3 son alternativos, se materializan como un
; unico patron CLIPS con sus 4 rule_ids OR'd (union de ?r2 y ?r3). El motor
; CLIPS ve dos patrones AND, equivalente a ?r1 AND (?r2 ∪ ?r3) y por tanto
; a ?r1 AND (?r2 OR ?r3). La estructura conceptual de 3 subconjuntos vive
; documentada aqui y en RULE_PROVENANCE['alerta-meta-proyecto-alto-riesgo']
; (campo `subconjuntos`), que es lo que consume la trazabilidad.
;
; Salience -10 garantiza que se evalua despues de las 17 alertas base.
(defrule alerta-meta-proyecto-alto-riesgo
  (declare (salience -10))
  ; Subconjunto ?r1 (obligatorio): riesgo geometrico de la zanja.
  (alerta (rule_id ?r1&:(or (eq ?r1 "alerta-seguridad-critica")
                            (eq ?r1 "alerta-blindaje-necesario"))))
  ; Subconjuntos ?r2 (urbano denso) OR ?r3 (amianto), alternativos.
  (alerta (rule_id ?ralt&:(or (eq ?ralt "alerta-trafico-sin-conduccion-provisional")
                              (eq ?ralt "alerta-fibrocemento-sin-gestion")
                              (eq ?ralt "alerta-amianto-sin-margen-seguridad"))))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Proyecto de alto riesgo: combina obra profunda con tramo urbano denso o amianto. Revisa el conjunto.")
                  (rule_id "alerta-meta-proyecto-alto-riesgo")
                  (fuente "regla agregada (combina otras alertas)"))))
"""
