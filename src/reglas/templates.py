"""
Definiciones CLIPS: templates (esquema de hechos) y reglas de elegibilidad.

Separado en su propio módulo para que las reglas sean fáciles de localizar,
leer y modificar sin tocar la lógica de carga/ejecución del motor.

Convención de sentinel: el valor "*" representa NULL en campos STRING de CLIPS.
Un item con red="*" aplica a cualquier red; con instalacion="*" a cualquier instalación.
"""

# Valor centinela para representar NULL en campos STRING de CLIPS
NULL_SENTINEL = "*"

# ---------------------------------------------------------------------------
# Templates (esquema de hechos)
# ---------------------------------------------------------------------------

TEMPLATES = """
(deftemplate datos-tuberia
  (slot tipo        (type STRING))
  (slot diametro_mm (type INTEGER))
  (slot red         (type STRING)))

(deftemplate datos-zanja
  (slot profundidad (type FLOAT))
  (slot red         (type STRING)))

(deftemplate datos-instalacion
  (slot instalacion (type STRING)))

(deftemplate datos-desmontaje
  (slot tipo_desmontaje (type STRING)))

(deftemplate item-entibacion
  (slot idx      (type INTEGER))
  (slot red      (type STRING))
  (slot umbral_m (type FLOAT)))

(deftemplate item-pozo
  (slot idx             (type INTEGER))
  (slot red             (type STRING))
  (slot profundidad_max (type FLOAT))
  (slot dn_max          (type INTEGER)))

(deftemplate item-valvuleria
  (slot idx        (type INTEGER))
  (slot dn_min     (type INTEGER))
  (slot dn_max     (type INTEGER))
  (slot instalacion (type STRING)))

(deftemplate item-desmontaje
  (slot idx              (type INTEGER))
  (slot es_fibrocemento  (type INTEGER))
  (slot dn_max           (type INTEGER)))

(deftemplate candidato-entibacion
  (slot idx (type INTEGER)))

(deftemplate candidato-pozo
  (slot idx (type INTEGER)))

(deftemplate candidato-valvuleria
  (slot idx (type INTEGER)))

(deftemplate candidato-desmontaje
  (slot idx (type INTEGER)))
"""

# ---------------------------------------------------------------------------
# Reglas de elegibilidad
# ---------------------------------------------------------------------------

RULES = """
; ── Entibación ──────────────────────────────────────────────────────────────
; Un item es candidato si:
;   - Su red coincide con la del proyecto O es wildcard "*"
;   - La profundidad de la zanja es ESTRICTAMENTE mayor que su umbral
(defrule entibacion-elegible
  (datos-zanja (profundidad ?p) (red ?red-proyecto))
  (item-entibacion (idx ?i) (red ?r) (umbral_m ?u))
  (test (or (eq ?r "*") (eq ?r ?red-proyecto)))
  (test (> ?p ?u))
  =>
  (assert (candidato-entibacion (idx ?i))))

; ── Pozo de registro ────────────────────────────────────────────────────────
; Un item es candidato si:
;   - Su red coincide O es wildcard
;   - profundidad < profundidad_max (sentinel 9999.0 = sin límite)
;   - diametro_mm <= dn_max        (sentinel 99999  = sin límite)
(defrule pozo-elegible
  (datos-tuberia (diametro_mm ?dn) (red ?red-proyecto))
  (datos-zanja   (profundidad ?p))
  (item-pozo (idx ?i) (red ?r) (profundidad_max ?pmax) (dn_max ?dmax))
  (test (or (eq ?r "*") (eq ?r ?red-proyecto)))
  (test (< ?p ?pmax))
  (test (<= ?dn ?dmax))
  =>
  (assert (candidato-pozo (idx ?i))))

; ── Valvulería ──────────────────────────────────────────────────────────────
; Un item es candidato si:
;   - dn_min <= diametro_mm <= dn_max
;   - Su instalación coincide O es wildcard
(defrule valvuleria-elegible
  (datos-tuberia    (diametro_mm ?dn))
  (datos-instalacion (instalacion ?inst))
  (item-valvuleria (idx ?i) (dn_min ?dmin) (dn_max ?dmax) (instalacion ?vinst))
  (test (<= ?dmin ?dn))
  (test (<= ?dn ?dmax))
  (test (or (eq ?vinst "*") (eq ?vinst ?inst)))
  =>
  (assert (candidato-valvuleria (idx ?i))))

; ── Desmontaje normal ────────────────────────────────────────────────────────
(defrule desmontaje-elegible-normal
  (datos-desmontaje (tipo_desmontaje "normal"))
  (datos-tuberia    (diametro_mm ?dn))
  (item-desmontaje  (idx ?i) (es_fibrocemento 0) (dn_max ?dmax))
  (test (<= ?dn ?dmax))
  =>
  (assert (candidato-desmontaje (idx ?i))))

; ── Desmontaje fibrocemento ──────────────────────────────────────────────────
(defrule desmontaje-elegible-fibrocemento
  (datos-desmontaje (tipo_desmontaje "fibrocemento"))
  (item-desmontaje  (idx ?i) (es_fibrocemento 1))
  =>
  (assert (candidato-desmontaje (idx ?i))))
"""
