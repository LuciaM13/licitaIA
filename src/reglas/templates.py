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
;   - La profundidad de la zanja es MAYOR O IGUAL que su umbral.
;     Se usa >= (no >) porque el Excel SAN usa la frontera 2.5m de forma
;     inclusiva: IF(D19<2.5, precio_superficial, precio_profundo) hace que
;     P=2.5 aplique el precio profundo. Con > estricto, P=2.5 seleccionaba
;     el item superficial (umbral=1.4) en lugar del profundo (umbral=2.5).
;     Efecto colateral mínimo: P=1.5 ABA y P=1.4 SAN (valores exactos) ahora
;     generan entibación; el Excel no la genera, pero es una conservadora
;     sobreestimación de muy bajo impacto práctico.
(defrule entibacion-elegible
  (datos-zanja (profundidad ?p) (red ?red-proyecto))
  (item-entibacion (idx ?i) (red ?r) (umbral_m ?u))
  (test (or (eq ?r "*") (eq ?r ?red-proyecto)))
  (test (>= ?p ?u))
  =>
  (assert (candidato-entibacion (idx ?i))))

; ── Pozo de registro ────────────────────────────────────────────────────────
; Un item es candidato si:
;   - Su red coincide O es wildcard
;   - profundidad <= profundidad_max (sentinel 9999.0 = sin límite)
;     Nota: se usa <= (no <) porque los rangos de profundidad en la BD son
;     inclusivos en el extremo superior (P<5m cubre exactamente P=5.0m).
;     Con < estricto, P=5.0m caía al pozo genérico ABA (intervalo 100m)
;     en vez del pozo SAN correcto (intervalo 32m). Bug detectado 2026-04-11.
;   - diametro_mm <= dn_max        (sentinel 99999  = sin límite)
(defrule pozo-elegible
  (datos-tuberia (diametro_mm ?dn) (red ?red-proyecto))
  (datos-zanja   (profundidad ?p))
  (item-pozo (idx ?i) (red ?r) (profundidad_max ?pmax) (dn_max ?dmax))
  (test (or (eq ?r "*") (eq ?r ?red-proyecto)))
  (test (<= ?p ?pmax))
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
; No se filtra por diámetro (a diferencia del desmontaje normal) porque el
; coste de demolición de fibrocemento lo domina el tratamiento del amianto,
; no el tamaño de la tubería - el precio es único e independiente del DN.
(defrule desmontaje-elegible-fibrocemento
  (datos-desmontaje (tipo_desmontaje "fibrocemento"))
  (item-desmontaje  (idx ?i) (es_fibrocemento 1))
  =>
  (assert (candidato-desmontaje (idx ?i))))
"""

# ---------------------------------------------------------------------------
# Templates y reglas de ALERTAS de validación técnica
# ---------------------------------------------------------------------------

TEMPLATES_ALERTAS = """
(deftemplate datos-proyecto
  (slot aba_activa        (type INTEGER))
  (slot san_activa        (type INTEGER))
  (slot aba_longitud_m    (type FLOAT))
  (slot aba_profundidad_m (type FLOAT))
  (slot san_profundidad_m (type FLOAT))
  (slot acometidas_aba_n  (type INTEGER))
  (slot desmontaje_tipo   (type STRING))
  (slot pct_seguridad     (type FLOAT))
  (slot pct_gestion       (type FLOAT)))

(deftemplate alerta
  (slot nivel (type STRING))
  (slot msg   (type STRING)))
"""

RULES_ALERTAS = """
; ── Fibrocemento sin gestión ambiental ──────────────────────────────────────
; RD 396/2006 obliga a plan de trabajo con amianto.
(defrule fibrocemento-sin-gestion
  (datos-proyecto (desmontaje_tipo "fibrocemento") (pct_gestion ?g&:(= ?g 0.0)))
  =>
  (assert (alerta (nivel "error")
                  (msg "Desmontaje de fibrocemento con Gestion Ambiental al 0%. El RD 396/2006 obliga a plan de trabajo con amianto. Revisa el porcentaje de Gestion Ambiental antes de licitar."))))

; ── Profundidad elevada con S&S bajo ───────────────────────────────────────
; A partir de 4 m se recomienda apeo especial o blindaje metálico.
(defrule excavacion-profunda-ss-bajo
  (datos-proyecto (aba_profundidad_m ?pa) (san_profundidad_m ?ps) (pct_seguridad ?s&:(< ?s 0.02)))
  (test (> (max ?pa ?ps) 4.0))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Excavacion con profundidad superior a 4 m y Seguridad y Salud inferior al 2%. A partir de 4 m conviene revisar la necesidad de apeo especial o blindaje metalico."))))

; ── Longitud ABA significativa sin acometidas ──────────────────────────────
(defrule longitud-aba-sin-acometidas
  (datos-proyecto (aba_activa 1) (aba_longitud_m ?l&:(> ?l 200.0)) (acometidas_aba_n ?n&:(= ?n 0)))
  =>
  (assert (alerta (nivel "warning")
                  (msg "Red ABA con mas de 200 m y 0 acometidas. Verifica si existen acometidas existentes en el tramo."))))

; ── ABA y SAN con profundidades similares ──────────────────────────────────
(defrule zanjas-profundidad-similar
  (datos-proyecto (aba_activa 1) (san_activa 1)
                  (aba_profundidad_m ?pa) (san_profundidad_m ?ps))
  (test (< (abs (- ?pa ?ps)) 0.3))
  =>
  (assert (alerta (nivel "info")
                  (msg "ABA y SAN con profundidades similares. Si van en zanja compartida, revisa si la entibacion debe presupuestarse como partida unica en lugar de doble."))))
"""
