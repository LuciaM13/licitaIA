"""
Base de conocimiento del sistema experto (CLIPS).

Único núcleo CLIPS del sistema. Describe el comportamiento del experto sobre
los parámetros del proyecto: primero clasifica la obra emitiendo **etiquetas**
(hechos derivados, p. ej. "zanja-compleja"), luego emite **alertas** al
licitador que pueden apoyarse en esas etiquetas (inferencia encadenada).

Las decisiones de elegibilidad de materiales viven en ``src/reglas/elegibilidad.py``
(Python puro, sin inferencia). Este módulo se ocupa solo de la parte IA real.

Vocabulario:
  - ``severidad`` (alta|media|baja) = gravedad de la clasificación del proyecto
    (color del badge en UI).
  - ``nivel`` (error|warning|info) = urgencia de la alerta para el licitador
    (icono de la alerta en UI).
  Son dimensiones independientes y no deben confundirse.

Convención de fuentes: el slot ``fuente`` de etiquetas y alertas guarda la
cita documental ("Excel EMASESA", "RD 396/2006", "regla interna",
"provisional") para trazabilidad y tooltip. El cuerpo del ``msg`` de cada
alerta NO debe contener citas normativas — el texto visible se mantiene corto
y en lenguaje llano.
"""

# Re-export para compatibilidad: el valor canónico vive en src.domain.constantes.
from src.domain.constantes import NULL_SENTINEL  # noqa: E402, F401


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
  (slot pct_servicios_afectados (type FLOAT))
  (slot conduccion_provisional_m (type FLOAT))
  (slot pozos_existentes_aba    (type STRING))
  (slot pozos_existentes_san    (type STRING))
  (slot instalacion_valvuleria  (type STRING)))

(deftemplate etiqueta
  (slot id        (type STRING))
  (slot nombre    (type STRING))
  (slot severidad (type STRING))
  (slot fuente    (type STRING)))

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
; ║  CAPA 1 — REGLAS DE CLASIFICACIÓN (emiten etiquetas desde inputs)       ║
; ╚══════════════════════════════════════════════════════════════════════════╝

; ── Zanja compleja ─────────────────────────────────────────────────────────
; Profundidad ABA o SAN > umbral. Provisional (pdte EMASESA).
(defrule clasificar-zanja-compleja
  (datos-proyecto (aba_profundidad_m ?pa) (san_profundidad_m ?ps))
  (test (> (max ?pa ?ps) {UMBRALES['zanja_compleja_prof_m']}))
  =>
  (assert (etiqueta (id "zanja-compleja")
                    (nombre "Obra compleja")
                    (severidad "alta")
                    (fuente "provisional"))))

; ── Tramo urbano denso ─────────────────────────────────────────────────────
; Longitud ABA alta y muchas acometidas → denso.
(defrule clasificar-tramo-urbano-denso
  (datos-proyecto (aba_activa 1)
                  (aba_longitud_m ?l&:(> ?l {UMBRALES['tramo_urbano_longitud_m']}))
                  (acometidas_aba_n ?n&:(> ?n {UMBRALES['tramo_urbano_acometidas_min']})))
  =>
  (assert (etiqueta (id "tramo-urbano-denso")
                    (nombre "Tramo urbano denso")
                    (severidad "media")
                    (fuente "provisional"))))

; ── Obra regulada por amianto ──────────────────────────────────────────────
; Desmontaje de fibrocemento → régimen amianto (RD 396/2006).
(defrule clasificar-obra-regulada-amianto
  (datos-proyecto (desmontaje_tipo "fibrocemento"))
  =>
  (assert (etiqueta (id "obra-regulada-amianto")
                    (nombre "Regulada por amianto")
                    (severidad "alta")
                    (fuente "RD 396/2006"))))

; ── Zanja compartida probable ──────────────────────────────────────────────
; ABA y SAN con profundidades similares → probablemente van en la misma zanja.
(defrule clasificar-zanja-compartida-probable
  (datos-proyecto (aba_activa 1) (san_activa 1)
                  (aba_profundidad_m ?pa) (san_profundidad_m ?ps))
  (test (< (abs (- ?pa ?ps)) {UMBRALES['zanja_compartida_delta_m']}))
  =>
  (assert (etiqueta (id "zanja-compartida-probable")
                    (nombre "Zanja compartida probable")
                    (severidad "baja")
                    (fuente "regla interna"))))

; ── Intervención en infraestructura existente ──────────────────────────────
; Hay pozos preexistentes a tratar (demolición o anulación) en ABA o SAN.
; Única regla con test (or ...) para que solo se dispare una vez aunque
; ambos campos sean distintos de "none".
(defrule clasificar-intervencion-infraestructura
  (datos-proyecto (pozos_existentes_aba ?pa) (pozos_existentes_san ?ps))
  (test (or (neq ?pa "none") (neq ?ps "none")))
  =>
  (assert (etiqueta (id "intervencion-infraestructura")
                    (nombre "Intervencion en infraestructura")
                    (severidad "media")
                    (fuente "regla interna"))))

; ╔══════════════════════════════════════════════════════════════════════════╗
; ║  CAPA 2 — REGLAS DE CLASIFICACIÓN DE 2º NIVEL (leen otras etiquetas)    ║
; ╚══════════════════════════════════════════════════════════════════════════╝

; ── Proyecto de alto riesgo ────────────────────────────────────────────────
; Obra compleja combinada con urbano denso o régimen amianto.
; Encadenamiento real: esta regla NO mira inputs, mira conclusiones previas.
(defrule clasificar-proyecto-alto-riesgo
  (etiqueta (id "zanja-compleja"))
  (or (etiqueta (id "tramo-urbano-denso"))
      (etiqueta (id "obra-regulada-amianto")))
  =>
  (assert (etiqueta (id "proyecto-alto-riesgo")
                    (nombre "Proyecto de alto riesgo")
                    (severidad "alta")
                    (fuente "regla interna (combina otras)"))))

; ╔══════════════════════════════════════════════════════════════════════════╗
; ║  CAPA 3 — REGLAS DE ALERTA (al licitador, en lenguaje llano)            ║
; ╚══════════════════════════════════════════════════════════════════════════╝

; ── Fibrocemento sin gestión ambiental ─────────────────────────────────────
; Apoyada en etiqueta "obra-regulada-amianto" (encadenamiento).
(defrule alerta-fibrocemento-sin-gestion
  (etiqueta (id "obra-regulada-amianto"))
  (datos-proyecto (pct_gestion ?g&:(= ?g 0.0)))
  =>
  (assert (alerta (nivel "error")
                  (msg "Hay fibrocemento pero la Gestion Ambiental esta al 0%. Revisa ese porcentaje.")
                  (rule_id "alerta-fibrocemento-sin-gestion")
                  (fuente "RD 396/2006"))))

; ── Seguridad crítica en obra compleja ─────────────────────────────────────
; S&S por debajo del umbral crítico en obra ya clasificada como compleja.
(defrule alerta-seguridad-critica
  (etiqueta (id "zanja-compleja"))
  (datos-proyecto (pct_seguridad ?s&:(< ?s {UMBRALES['ss_critico_pct']})))
  =>
  (assert (alerta (nivel "error")
                  (msg "Obra profunda con la partida de Seguridad muy baja. Revisala antes de licitar.")
                  (rule_id "alerta-seguridad-critica")
                  (fuente "Excel EMASESA"))))

; ── Blindaje recomendado ───────────────────────────────────────────────────
; S&S en rango bajo (2%-3%) sobre obra compleja: revisar blindaje.
; Umbral estricto inferior (>= ss_critico_pct) para evitar solape con la alerta crítica.
(defrule alerta-blindaje-necesario
  (etiqueta (id "zanja-compleja"))
  (datos-proyecto (pct_seguridad ?s&:(>= ?s {UMBRALES['ss_critico_pct']})
                                  &:(< ?s  {UMBRALES['ss_bajo_obra_compleja_pct']})))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Obra compleja con poco margen de Seguridad. Revisa el blindaje.")
                  (rule_id "alerta-blindaje-necesario")
                  (fuente "Excel EMASESA"))))

; ── ABA larga sin acometidas ───────────────────────────────────────────────
; No necesita etiqueta: el caso es directo sobre inputs.
(defrule alerta-aba-larga-sin-acometidas
  (datos-proyecto (aba_activa 1)
                  (aba_longitud_m ?l&:(> ?l {UMBRALES['aba_larga_longitud_m']}))
                  (acometidas_aba_n ?n&:(= ?n 0)))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Red ABA larga sin acometidas. Has comprobado si existen?")
                  (rule_id "alerta-aba-larga-sin-acometidas")
                  (fuente "regla interna"))))

; ── Coordinación de servicios ──────────────────────────────────────────────
; Encadenamiento: dos etiquetas de 1er nivel combinan en nueva alerta.
(defrule alerta-coordinacion-servicios
  (etiqueta (id "tramo-urbano-denso"))
  (etiqueta (id "intervencion-infraestructura"))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Tramo urbano con muchos servicios. Falta partida de coordinacion?")
                  (rule_id "alerta-coordinacion-servicios")
                  (fuente "regla interna"))))

; ── Entibación duplicada (zanja compartida) ───────────────────────────────
(defrule alerta-entibacion-doble
  (etiqueta (id "zanja-compartida-probable"))
  =>
  (assert (alerta (nivel "warning")
                  (msg "ABA y SAN a la misma profundidad. Entibacion por duplicado?")
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
"""
