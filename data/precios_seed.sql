BEGIN TRANSACTION;
CREATE TABLE "acerados" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                red    TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
                label  TEXT NOT NULL,
                unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'm3', 'ud')),
                precio INTEGER NOT NULL CHECK(precio > 0),
                factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
                UNIQUE(red, label)
            );
INSERT INTO "acerados" VALUES(2081,'ABA','Baldosa cigarrillo','m2',1075,1.0);
INSERT INTO "acerados" VALUES(2082,'ABA','Baldosa granallada','m2',2389,1.0);
INSERT INTO "acerados" VALUES(2083,'ABA','Baldosa hexagonal','m2',1550,1.0);
INSERT INTO "acerados" VALUES(2084,'ABA','Baldosa hidráulica 40x40x4','m2',1213,1.0);
INSERT INTO "acerados" VALUES(2085,'ABA','Baldosa terrazo 40x40','m2',1736,1.0);
INSERT INTO "acerados" VALUES(2086,'ABA','Granito','m2',8780,1.0);
INSERT INTO "acerados" VALUES(2087,'ABA','Hormigón','m2',5028,1.0);
INSERT INTO "acerados" VALUES(2088,'ABA','Losa hidráulica','m2',3890,1.0);
INSERT INTO "acerados" VALUES(2089,'ABA','Losa terrazo','m2',4086,1.0);
INSERT INTO "acerados" VALUES(2090,'ABA','Plaquetas de gres','m2',16603,1.0);
INSERT INTO "acerados" VALUES(2091,'SAN','Baldosa cigarrillo','m2',1075,1.0);
INSERT INTO "acerados" VALUES(2092,'SAN','Baldosa granallada','m2',2389,1.0);
INSERT INTO "acerados" VALUES(2093,'SAN','Baldosa hexagonal','m2',1550,1.0);
INSERT INTO "acerados" VALUES(2094,'SAN','Baldosa hidráulica 40x40x4','m2',1213,1.0);
INSERT INTO "acerados" VALUES(2095,'SAN','Baldosa terrazo 40x40','m2',1736,1.0);
INSERT INTO "acerados" VALUES(2096,'SAN','Granito','m2',8064,1.0);
INSERT INTO "acerados" VALUES(2097,'SAN','Hormigón','m2',5028,1.0);
INSERT INTO "acerados" VALUES(2098,'SAN','Losa hidráulica','m2',3537,1.0);
INSERT INTO "acerados" VALUES(2099,'SAN','Losa terrazo','m2',4114,1.0);
INSERT INTO "acerados" VALUES(2100,'SAN','Plaquetas de gres','m2',16603,1.0);
CREATE TABLE acometida_defecto (
    red  TEXT PRIMARY KEY CHECK(red IN ('ABA', 'SAN')),
    tipo TEXT NOT NULL
);
INSERT INTO "acometida_defecto" VALUES('ABA','Con demolición (<6m)');
INSERT INTO "acometida_defecto" VALUES('SAN','Adaptación gres');
CREATE TABLE "acometidas" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
                tipo  TEXT NOT NULL,
                precio INTEGER NOT NULL CHECK(precio > 0),
                factor_piezas REAL NOT NULL DEFAULT 1.0 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
                UNIQUE(red, tipo)
            );
INSERT INTO "acometidas" VALUES(937,'ABA','Con demolición (<6m)',39851,1.2);
INSERT INTO "acometidas" VALUES(938,'ABA','Con demolición (>6m)',44265,1.2);
INSERT INTO "acometidas" VALUES(939,'ABA','Sin demolición (<6m)',21783,1.2);
INSERT INTO "acometidas" VALUES(940,'SAN','Adaptación PVC',42537,1.0);
INSERT INTO "acometidas" VALUES(941,'SAN','Adaptación gres',46231,1.0);
INSERT INTO "acometidas" VALUES(942,'SAN','Reposición PVC <6m',84297,1.0);
INSERT INTO "acometidas" VALUES(943,'SAN','Reposición PVC >6m',121789,1.0);
INSERT INTO "acometidas" VALUES(944,'SAN','Reposición gres <6m',117313,1.0);
INSERT INTO "acometidas" VALUES(945,'SAN','Reposición gres >6m',167584,1.0);
CREATE TABLE audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    categoria   TEXT NOT NULL,      -- e.g. "catalogo_aba", "excavacion", "imbornales"
    clave       TEXT NOT NULL,      -- identificador del ítem dentro de la categoría
    operacion   TEXT NOT NULL CHECK(operacion IN ('INSERT', 'UPDATE', 'DELETE')),
    antes_json  TEXT,                -- NULL en INSERT
    despues_json TEXT,               -- NULL en DELETE
    actor       TEXT NOT NULL DEFAULT 'desconocido'
);
INSERT INTO "audit_log" VALUES(1,'2026-04-19 15:46:02','catalogo_aba','FD  80 mm','UPDATE','{"label": "FD  80 mm", "tipo": "FD", "diametro_mm": 80, "precio_m": 43.25, "factor_piezas": 1.2, "precio_material_m": 12.76}','{"label": "FD  80 mm", "tipo": "FD", "diametro_mm": 80, "precio_m": 43.75, "factor_piezas": 1.2, "precio_material_m": 12.76}','test_script');
INSERT INTO "audit_log" VALUES(2,'2026-04-19 15:46:02','catalogo_aba','FD  80 mm','UPDATE','{"label": "FD  80 mm", "tipo": "FD", "diametro_mm": 80, "precio_m": 43.75, "factor_piezas": 1.2, "precio_material_m": 12.76}','{"label": "FD  80 mm", "tipo": "FD", "diametro_mm": 80, "precio_m": 43.25, "factor_piezas": 1.2, "precio_material_m": 12.76}','test_restore');
CREATE TABLE "bordillos" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label  TEXT NOT NULL UNIQUE,
                unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'ud')),
                precio INTEGER NOT NULL CHECK(precio > 0),
                factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0)
            );
INSERT INTO "bordillos" VALUES(417,'Bordillo bicapa 10x20','m',937,1.0);
INSERT INTO "bordillos" VALUES(418,'Bordillo bicapa 17x28','m',1546,1.0);
INSERT INTO "bordillos" VALUES(419,'Bordillo de hormigón','m',1524,1.0);
INSERT INTO "bordillos" VALUES(420,'Bordillo granítico','m',2181,1.0);
CREATE TABLE "calzadas" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label  TEXT NOT NULL UNIQUE,
                unidad TEXT NOT NULL CHECK(unidad IN ('m2', 'm3')),
                precio INTEGER NOT NULL CHECK(precio > 0),
                factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0)
            );
INSERT INTO "calzadas" VALUES(521,'Adoquín','m2',3355,1.0);
INSERT INTO "calzadas" VALUES(522,'Aglomerado','m3',13299,1.0);
INSERT INTO "calzadas" VALUES(523,'Base zahorra','m3',2234,1.0);
INSERT INTO "calzadas" VALUES(524,'Capa base pavimento','m3',11175,1.0);
INSERT INTO "calzadas" VALUES(525,'Hormigón','m3',11160,1.0);
CREATE TABLE config (
    clave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);
INSERT INTO "config" VALUES('pct_gg',0.13);
INSERT INTO "config" VALUES('pct_bi',0.06);
INSERT INTO "config" VALUES('pct_iva',0.21);
INSERT INTO "config" VALUES('factor_esponjamiento',1.3);
INSERT INTO "config" VALUES('pct_manual_defecto',0.3);
INSERT INTO "config" VALUES('conduccion_provisional_precio_m',11.43);
INSERT INTO "config" VALUES('pct_ci',1.05);
CREATE TABLE defaults_ui (
    clave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);
INSERT INTO "defaults_ui" VALUES('aba_longitud_m',100.0);
INSERT INTO "defaults_ui" VALUES('aba_profundidad_m',1.2);
INSERT INTO "defaults_ui" VALUES('san_longitud_m',132.0);
INSERT INTO "defaults_ui" VALUES('san_profundidad_m',1.6);
INSERT INTO "defaults_ui" VALUES('pav_aba_acerado_m2',390.0);
INSERT INTO "defaults_ui" VALUES('pav_aba_bordillo_m',310.0);
INSERT INTO "defaults_ui" VALUES('pav_san_calzada_m2',760.0);
INSERT INTO "defaults_ui" VALUES('pav_san_acera_m2',390.0);
INSERT INTO "defaults_ui" VALUES('acometidas_n',26.0);
INSERT INTO "defaults_ui" VALUES('pct_seguridad',0.03);
INSERT INTO "defaults_ui" VALUES('pct_gestion',0.0);
INSERT INTO "defaults_ui" VALUES('conduccion_provisional_m',0.0);
CREATE TABLE "demolicion" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
                label TEXT NOT NULL,
                unidad TEXT NOT NULL CHECK(unidad IN ('m', 'm2', 'm3', 'ud')),
                material TEXT NOT NULL DEFAULT 'generico',
                precio INTEGER NOT NULL CHECK(precio > 0),
                factor_ci REAL NOT NULL DEFAULT 1.0 CHECK(factor_ci > 0),
                UNIQUE(red, unidad, material)
            );
INSERT INTO "demolicion" VALUES(865,'ABA','Demolición acerado hormigón','m2','hormigon_acerado',1400,1.0);
INSERT INTO "demolicion" VALUES(866,'ABA','Demolición acerado losa hidráulica','m2','losa_hidraulica',1400,1.0);
INSERT INTO "demolicion" VALUES(867,'ABA','Demolición acerado losa terrazo','m2','losa_terrazo',1400,1.0);
INSERT INTO "demolicion" VALUES(868,'ABA','Demolición bordillo','m','generico',403,1.0);
INSERT INTO "demolicion" VALUES(869,'ABA','Demolición bordillo granítico','m','granitico',532,1.0);
INSERT INTO "demolicion" VALUES(870,'ABA','Demolición bordillo hidráulico','m','hidraulico',423,1.0);
INSERT INTO "demolicion" VALUES(871,'ABA','Demolición calzada','m2','generico',1296,1.0);
INSERT INTO "demolicion" VALUES(872,'ABA','Demolición calzada adoquín','m2','adoquin',1505,1.0);
INSERT INTO "demolicion" VALUES(873,'ABA','Demolición calzada aglomerado','m2','aglomerado',1361,1.0);
INSERT INTO "demolicion" VALUES(874,'ABA','Demolición calzada hormigón','m2','hormigon',1660,1.0);
INSERT INTO "demolicion" VALUES(875,'SAN','Demolición acerado hormigón','m2','hormigon_acerado',1400,1.0);
INSERT INTO "demolicion" VALUES(876,'SAN','Demolición acerado losa hidráulica','m2','losa_hidraulica',1400,1.0);
INSERT INTO "demolicion" VALUES(877,'SAN','Demolición acerado losa terrazo','m2','losa_terrazo',1400,1.0);
INSERT INTO "demolicion" VALUES(878,'SAN','Demolición bordillo','m','generico',403,1.0);
INSERT INTO "demolicion" VALUES(879,'SAN','Demolición bordillo granítico','m','granitico',532,1.0);
INSERT INTO "demolicion" VALUES(880,'SAN','Demolición bordillo hidráulico','m','hidraulico',423,1.0);
INSERT INTO "demolicion" VALUES(881,'SAN','Demolición calzada','m2','generico',1296,1.0);
INSERT INTO "demolicion" VALUES(882,'SAN','Demolición calzada adoquín','m2','adoquin',1505,1.0);
INSERT INTO "demolicion" VALUES(883,'SAN','Demolición calzada aglomerado','m2','aglomerado',1361,1.0);
INSERT INTO "demolicion" VALUES(884,'SAN','Demolición calzada hormigón','m2','hormigon',1660,1.0);
CREATE TABLE "desmontaje" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label    TEXT NOT NULL UNIQUE,
                dn_max   INTEGER NOT NULL CHECK(dn_max > 0),
                precio_m INTEGER NOT NULL CHECK(precio_m > 0),
                es_fibrocemento INTEGER NOT NULL DEFAULT 0 CHECK(es_fibrocemento IN (0, 1))
            );
INSERT INTO "desmontaje" VALUES(304,'Desmontaje tubería DN<150mm',150,1275,0);
INSERT INTO "desmontaje" VALUES(305,'Desmontaje tubería DN<600mm',599,1687,0);
INSERT INTO "desmontaje" VALUES(306,'Desmontaje/demolición fibrocemento',9999,8636,1);
CREATE TABLE "entibacion" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label     TEXT NOT NULL UNIQUE,
                precio_m2 INTEGER NOT NULL CHECK(precio_m2 > 0),
                umbral_m  REAL NOT NULL CHECK(umbral_m > 0),
                red       TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN'))
            );
INSERT INTO "entibacion" VALUES(295,'Entibación blindada ABA',407,1.5,'ABA');
INSERT INTO "entibacion" VALUES(296,'Entibación blindada SAN',407,1.4,'SAN');
INSERT INTO "entibacion" VALUES(297,'Entibación blindada SAN profunda',2165,2.5,'SAN');
CREATE TABLE espesores_calzada (
    calzada_id INTEGER PRIMARY KEY REFERENCES calzadas(id)
               ON DELETE CASCADE,
    espesor_m  REAL NOT NULL
);
INSERT INTO "espesores_calzada" VALUES(522,0.12);
INSERT INTO "espesores_calzada" VALUES(523,0.2);
INSERT INTO "espesores_calzada" VALUES(524,0.15);
INSERT INTO "espesores_calzada" VALUES(525,0.15);
CREATE TABLE excavacion (
    clave TEXT PRIMARY KEY,
    valor REAL NOT NULL
);
INSERT INTO "excavacion" VALUES('mec_hasta_25',2.92381);
INSERT INTO "excavacion" VALUES('mec_mas_25',4.761905400000000733e+00);
INSERT INTO "excavacion" VALUES('manual_hasta_25',10.63999965);
INSERT INTO "excavacion" VALUES('manual_mas_25',13.32381015);
INSERT INTO "excavacion" VALUES('arrinonado',21.12381);
INSERT INTO "excavacion" VALUES('relleno',18.4699998);
INSERT INTO "excavacion" VALUES('carga_mec',0.32381);
INSERT INTO "excavacion" VALUES('transporte',5.04);
INSERT INTO "excavacion" VALUES('canon_tierras',1.5237999);
INSERT INTO "excavacion" VALUES('canon_mixto',11.990952);
INSERT INTO "excavacion" VALUES('umbral_profundidad_m',2.5);
CREATE TABLE "imbornales" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                precio INTEGER NOT NULL CHECK(precio > 0),
                tipo  TEXT NOT NULL CHECK(tipo IN ('adaptacion', 'nuevo'))
            );
INSERT INTO "imbornales" VALUES(506,'Adaptación imbornal',11429,'adaptacion');
INSERT INTO "imbornales" VALUES(507,'Imbornal buzón c/clapeta',83050,'nuevo');
INSERT INTO "imbornales" VALUES(508,'Imbornal buzón s/clapeta',76384,'nuevo');
INSERT INTO "imbornales" VALUES(509,'Imbornal nuevo rejilla c/clapeta',52189,'nuevo');
INSERT INTO "imbornales" VALUES(510,'Imbornal nuevo rejilla s/clapeta',52189,'nuevo');
CREATE TABLE "pozos" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label            TEXT NOT NULL,
                precio           INTEGER NOT NULL CHECK(precio > 0),
                intervalo        REAL NOT NULL CHECK(intervalo > 0),
                red              TEXT CHECK(red IS NULL OR red IN ('ABA', 'SAN')),
                profundidad_max  REAL CHECK(profundidad_max IS NULL OR profundidad_max > 0),
                dn_max           INTEGER CHECK(dn_max IS NULL OR dn_max > 0),
                precio_tapa      INTEGER NOT NULL DEFAULT 0 CHECK(precio_tapa >= 0),
                precio_tapa_material INTEGER NOT NULL DEFAULT 0 CHECK(precio_tapa_material >= 0),
                precio_pate_material INTEGER NOT NULL DEFAULT 0 CHECK(precio_pate_material >= 0)
            );
INSERT INTO "pozos" VALUES(3164,'Pozo prefabricado hormigón',22913,100.0,NULL,NULL,NULL,17544,0,0);
INSERT INTO "pozos" VALUES(3165,'Pozo registro SAN P<2.5m Tub≤500',102079,32.0,'SAN',2.5,500,0,15273,185);
INSERT INTO "pozos" VALUES(3166,'Pozo registro SAN P<2.5m Tub≤600',107103,32.0,'SAN',2.5,600,0,15273,185);
INSERT INTO "pozos" VALUES(3167,'Pozo registro SAN P<2.5m Tub≤800',157273,32.0,'SAN',2.5,800,0,15273,185);
INSERT INTO "pozos" VALUES(3168,'Pozo registro SAN P<2.5m Tub≤1000',223325,32.0,'SAN',2.5,1000,0,15273,185);
INSERT INTO "pozos" VALUES(3169,'Pozo registro SAN P<2.5m Tub≤1200',237321,32.0,'SAN',2.5,1200,0,15273,185);
INSERT INTO "pozos" VALUES(3170,'Pozo registro SAN P<3.5m Tub≤500',123030,32.0,'SAN',3.5,500,0,15273,185);
INSERT INTO "pozos" VALUES(3171,'Pozo registro SAN P<3.5m Tub≤600',128052,32.0,'SAN',3.5,600,0,15273,185);
INSERT INTO "pozos" VALUES(3172,'Pozo registro SAN P<3.5m Tub≤800',133996,32.0,'SAN',3.5,800,0,15273,185);
INSERT INTO "pozos" VALUES(3173,'Pozo registro SAN P<3.5m Tub≤1000',244273,32.0,'SAN',3.5,1000,0,15273,185);
INSERT INTO "pozos" VALUES(3174,'Pozo registro SAN P<3.5m Tub≤1200',257317,32.0,'SAN',3.5,1200,0,15273,185);
INSERT INTO "pozos" VALUES(3175,'Pozo registro SAN P<5m Tub≤500',148163,32.0,'SAN',5.0,500,0,15273,185);
INSERT INTO "pozos" VALUES(3176,'Pozo registro SAN P<5m Tub≤600',153189,32.0,'SAN',5.0,600,0,15273,185);
INSERT INTO "pozos" VALUES(3177,'Pozo registro SAN P<5m Tub≤800',157273,32.0,'SAN',5.0,800,0,15273,185);
INSERT INTO "pozos" VALUES(3178,'Pozo registro SAN P<5m Tub≤1000',270618,32.0,'SAN',5.0,1000,0,15273,185);
INSERT INTO "pozos" VALUES(3179,'Pozo registro SAN P<5m Tub≤1200',283690,32.0,'SAN',5.0,1200,0,15273,185);
INSERT INTO "pozos" VALUES(3180,'Pozo registro SAN P<2.5m Tub≤1500',308463,32.0,'SAN',2.5,1500,0,15273,185);
INSERT INTO "pozos" VALUES(3181,'Pozo registro SAN P<2.5m Tub≤1600',324264,32.0,'SAN',2.5,1600,0,15273,185);
INSERT INTO "pozos" VALUES(3182,'Pozo registro SAN P<2.5m Tub≤1800',369494,32.0,'SAN',2.5,1800,0,15273,185);
INSERT INTO "pozos" VALUES(3183,'Pozo registro SAN P<2.5m Tub≤2000',396989,32.0,'SAN',2.5,2000,0,15273,185);
INSERT INTO "pozos" VALUES(3184,'Pozo registro SAN P<2.5m Tub≤2500',495160,32.0,'SAN',2.5,9999,0,15273,185);
INSERT INTO "pozos" VALUES(3185,'Pozo registro SAN P<3.5m Tub≤1500',329839,32.0,'SAN',3.5,1500,0,15273,185);
INSERT INTO "pozos" VALUES(3186,'Pozo registro SAN P<3.5m Tub≤1600',345640,32.0,'SAN',3.5,1600,0,15273,185);
INSERT INTO "pozos" VALUES(3187,'Pozo registro SAN P<3.5m Tub≤1800',390871,32.0,'SAN',3.5,1800,0,15273,185);
INSERT INTO "pozos" VALUES(3188,'Pozo registro SAN P<3.5m Tub≤2000',417426,32.0,'SAN',3.5,2000,0,15273,185);
INSERT INTO "pozos" VALUES(3189,'Pozo registro SAN P<3.5m Tub≤2500',518020,32.0,'SAN',3.5,9999,0,15273,185);
INSERT INTO "pozos" VALUES(3190,'Pozo registro SAN P<5m Tub≤1500',356110,32.0,'SAN',5.0,1500,0,15273,185);
INSERT INTO "pozos" VALUES(3191,'Pozo registro SAN P<5m Tub≤1600',371911,32.0,'SAN',5.0,1600,0,15273,185);
INSERT INTO "pozos" VALUES(3192,'Pozo registro SAN P<5m Tub≤1800',417141,32.0,'SAN',5.0,1800,0,15273,185);
INSERT INTO "pozos" VALUES(3193,'Pozo registro SAN P<5m Tub≤2000',446131,32.0,'SAN',5.0,2000,0,15273,185);
INSERT INTO "pozos" VALUES(3194,'Pozo registro SAN P<5m Tub≤2500',544334,32.0,'SAN',5.0,9999,0,15273,185);
CREATE TABLE "pozos_existentes_precios" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
                accion TEXT NOT NULL CHECK(accion IN ('demolicion', 'anulacion')),
                precio INTEGER NOT NULL CHECK(precio > 0),
                intervalo_m REAL NOT NULL CHECK(intervalo_m > 0),
                UNIQUE(red, accion)
            );
INSERT INTO "pozos_existentes_precios" VALUES(405,'ABA','anulacion',42859,100.0);
INSERT INTO "pozos_existentes_precios" VALUES(406,'ABA','demolicion',5032,100.0);
INSERT INTO "pozos_existentes_precios" VALUES(407,'SAN','anulacion',63186,32.0);
INSERT INTO "pozos_existentes_precios" VALUES(408,'SAN','demolicion',5177,32.0);
CREATE TABLE presupuesto_capitulos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    presupuesto_id  INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
    capitulo        TEXT NOT NULL,      -- ej: "01 OBRA CIVIL ABASTECIMIENTO"
    subtotal        REAL NOT NULL,
    orden           INTEGER NOT NULL    -- para mantener el orden de capítulos
);
INSERT INTO "presupuesto_capitulos" VALUES(12,4,'01 OBRA CIVIL ABASTECIMIENTO',1.252065002086037749e+04,1);
INSERT INTO "presupuesto_capitulos" VALUES(13,4,'02 PAVIMENTACIÓN ABASTECIMIENTO',11810.699922,2);
INSERT INTO "presupuesto_capitulos" VALUES(14,4,'03 ACOMETIDAS ABASTECIMIENTO',13055.32800936,3);
INSERT INTO "presupuesto_capitulos" VALUES(15,4,'04 SEGURIDAD Y SALUD',1.046896437660310995e+03,4);
CREATE TABLE presupuesto_parametros (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    presupuesto_id  INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
    clave           TEXT NOT NULL,      -- ej: "aba_longitud_m", "san_tuberia"
    valor           TEXT NOT NULL       -- siempre TEXT para flexibilidad (números se parsean)
);
CREATE TABLE presupuesto_partidas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    capitulo_id INTEGER NOT NULL REFERENCES presupuesto_capitulos(id) ON DELETE CASCADE,
    descripcion TEXT NOT NULL,
    importe     REAL NOT NULL
);
INSERT INTO "presupuesto_partidas" VALUES(75,12,'FD  80 mm',5.189999975999999151e+03);
INSERT INTO "presupuesto_partidas" VALUES(76,12,'Excavación manual',2.57917741115863464e+02);
INSERT INTO "presupuesto_partidas" VALUES(77,12,'Excavación mecánica',1.651578345756359738e+02);
INSERT INTO "presupuesto_partidas" VALUES(78,12,'Apoyo y arriñonado',396.81312563655);
INSERT INTO "presupuesto_partidas" VALUES(79,12,'Relleno de albero',1.132007817742200132e+03);
INSERT INTO "presupuesto_partidas" VALUES(80,12,'Carga de tierras',25.85642408013);
INSERT INTO "presupuesto_partidas" VALUES(81,12,'Transporte a vertedero',4.072385519999999701e+02);
INSERT INTO "presupuesto_partidas" VALUES(82,12,'Canon vertido tierras',160.06);
INSERT INTO "presupuesto_partidas" VALUES(83,12,'Canon vertido mixto',440.67);
INSERT INTO "presupuesto_partidas" VALUES(84,12,'Pozo prefabricado hormigón',240.58999965);
INSERT INTO "presupuesto_partidas" VALUES(85,12,'Pozo prefabricado hormigón (tapa)',184.20999975);
INSERT INTO "presupuesto_partidas" VALUES(86,12,'Desagüe DN80 (tubería DN≤300)',274.174999875);
INSERT INTO "presupuesto_partidas" VALUES(87,12,'Conexión ɸ DN<100',7.20310000200000104e+02);
INSERT INTO "presupuesto_partidas" VALUES(88,12,'Ventosa trifuncional DN≤80-599',1.965713998500000343e+02);
INSERT INTO "presupuesto_partidas" VALUES(89,12,'Compuerta DN80-99',1.848571199999999805e+02);
INSERT INTO "presupuesto_partidas" VALUES(90,12,'Pozo de desagüe',654.815000175);
INSERT INTO "presupuesto_partidas" VALUES(91,12,'FD  80 mm (suministro)',1608.00003);
INSERT INTO "presupuesto_partidas" VALUES(92,12,'Ventosa trifuncional DN≤80-599 (material)',200.99999997);
INSERT INTO "presupuesto_partidas" VALUES(93,12,'Compuerta DN80-99 (material)',80.40000024);
INSERT INTO "presupuesto_partidas" VALUES(94,13,'Demolición acerado',3.04589990250000028e+03);
INSERT INTO "presupuesto_partidas" VALUES(95,13,'Demolición bordillo',1.31129986050000025e+03);
INSERT INTO "presupuesto_partidas" VALUES(96,13,'Baldosa cigarrillo',4403.1000195);
INSERT INTO "presupuesto_partidas" VALUES(97,13,'Bordillo bicapa 10x20',3050.4001395);
INSERT INTO "presupuesto_partidas" VALUES(98,14,'Acometidas ABA',13055.32800936);
INSERT INTO "presupuesto_partidas" VALUES(99,15,'Seguridad y Salud',1.046896437660310995e+03);
CREATE TABLE presupuesto_trazabilidad (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    presupuesto_id  INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
    red             TEXT NOT NULL,       -- "ABA" o "SAN"
    orden           INTEGER NOT NULL,    -- 0=Entibación, 1=Pozo, 2=Valvulería, 3=Desmontaje
    explicacion     TEXT NOT NULL        -- frase en castellano
);
INSERT INTO "presupuesto_trazabilidad" VALUES(1,4,'ABA',0,'La profundidad de la zanja (1,20 m) no supera el umbral de entibación (1,50 m en ABA), por lo tanto no se incluye entibación.');
INSERT INTO "presupuesto_trazabilidad" VALUES(2,4,'ABA',1,'Para DN=80 mm a 1,20 m en red ABA, se selecciona «Pozo prefabricado hormigón».');
INSERT INTO "presupuesto_trazabilidad" VALUES(3,4,'ABA',2,'Para DN=80 mm (instalación: enterrada) se incluyen 5 elementos de valvulería: «Desagüe DN80 (tubería DN≤300)», «Conexión ɸ DN<100», «Ventosa trifuncional DN≤80-599», «Compuerta DN80-99» y «Pozo de desagüe».');
INSERT INTO "presupuesto_trazabilidad" VALUES(4,4,'ABA',3,'No se ha indicado tubería existente a desmontar, por lo tanto no se incluye esta partida.');
CREATE TABLE presupuestos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    creado_en   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    descripcion TEXT NOT NULL DEFAULT '',
    -- Totales financieros
    pem         REAL NOT NULL,
    gg          REAL NOT NULL,
    bi          REAL NOT NULL,
    pbl_sin_iva REAL NOT NULL,
    iva         REAL NOT NULL,
    total       REAL NOT NULL,
    -- Porcentajes usados
    pct_gg      REAL NOT NULL,
    pct_bi      REAL NOT NULL,
    pct_iva     REAL NOT NULL,
    pct_ci      REAL NOT NULL DEFAULT 1.0
);
INSERT INTO "presupuestos" VALUES(4,'2026-04-12 11:38:41','',38433.57,4750.74,2192.65,45380.0,9529.8,54909.8,0.13,0.06,0.21,1.0);
CREATE TABLE schema_version (  version INTEGER PRIMARY KEY,  descripcion TEXT NOT NULL,  aplicada_en TEXT NOT NULL DEFAULT (datetime('now')));
INSERT INTO "schema_version" VALUES(1,'Columnas nuevas + datos iniciales por defecto','2026-04-11 21:33:38');
INSERT INTO "schema_version" VALUES(2,'Fix entibación SAN umbral 1.4m y desmontaje DN=150 frontera','2026-04-12 08:50:25');
INSERT INTO "schema_version" VALUES(3,'Añadir entibación SAN profunda P>=2.5m (22.73 €/m²)','2026-04-12 13:56:14');
INSERT INTO "schema_version" VALUES(4,'Fix dem acerado base 7.44→14.0; pozos SAN dn_max 2500→9999 para DN>=3000','2026-04-12 14:10:57');
INSERT INTO "schema_version" VALUES(5,'Eliminar ''Entibación tipo paralelo'' (dead code): profunda SAN ya cubierta por ''Entibación blindada SAN profunda''','2026-04-12 16:00:44');
INSERT INTO "schema_version" VALUES(6,'Fix precios entibación: base 3.037→4.067 (superf) y 16.167→21.648 (profunda). Los anteriores usaban factor ~1.406 en vez de CI=1.05','2026-04-13 18:59:08');
INSERT INTO "schema_version" VALUES(7,'Deduplicar demolicion (red, unidad) y añadir unique index','2026-04-15 14:40:22');
INSERT INTO "schema_version" VALUES(8,'Fix drift Patrón A (18 precios ratio 1.05²) + Gres SAN DN300 aislado','2026-04-19 12:23:54');
INSERT INTO "schema_version" VALUES(9,'Fix residual mec_hasta_25 (2.92→2.9238) para invariante BD × 1.05 = 3.07','2026-04-19 12:28:28');
INSERT INTO "schema_version" VALUES(10,'Fix Patrón B imbornales (ratio 1.05³) alineado con Excel oficial','2026-04-19 13:22:37');
INSERT INTO "schema_version" VALUES(11,'Fix residuales Patrón A en excavación (carga_mec, arrinonado)','2026-04-19 13:28:31');
INSERT INTO "schema_version" VALUES(12,'CHECK constraints completos en tablas de precios (defensa en profundidad)','2026-04-19 13:31:56');
INSERT INTO "schema_version" VALUES(13,'Precios a INTEGER céntimos (2 decimales exactos, sin error de float)','2026-04-19 13:38:54');
INSERT INTO "schema_version" VALUES(14,'Tabla audit_log para trazabilidad (escritura desde guardar_todo)','2026-04-19 13:43:36');
INSERT INTO "schema_version" VALUES(15,'Demolición con variantes por material (granitico/hidraulico/adoquin/etc.)','2026-04-19 13:50:21');
INSERT INTO "schema_version" VALUES(16,'Añadir SAN bordillo generico (fallback legacy, mismo precio que ABA)','2026-04-19 14:10:09');
CREATE TABLE "subbases" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                precio_m3 INTEGER NOT NULL CHECK(precio_m3 > 0)
            );
INSERT INTO "subbases" VALUES(205,'Base albero compactado',1823);
INSERT INTO "subbases" VALUES(206,'Base hormigon acerado',10777);
CREATE TABLE "tuberias" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                red   TEXT NOT NULL CHECK(red IN ('ABA', 'SAN')),
                label TEXT NOT NULL,
                tipo  TEXT NOT NULL,
                diametro_mm  INTEGER NOT NULL CHECK(diametro_mm > 0),
                precio_m     INTEGER NOT NULL CHECK(precio_m > 0),
                factor_piezas     REAL NOT NULL DEFAULT 1.0 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
                precio_material_m INTEGER NOT NULL DEFAULT 0 CHECK(precio_material_m >= 0),
                UNIQUE(red, label)
            );
INSERT INTO "tuberias" VALUES(4241,'ABA','FD  80 mm','FD',80,4325,1.2,1276);
INSERT INTO "tuberias" VALUES(4242,'ABA','PE-100 Ø 90 mm','PE-100',90,1049,1.2,232);
INSERT INTO "tuberias" VALUES(4243,'ABA','FD  100 mm','FD',100,4553,1.2,1505);
INSERT INTO "tuberias" VALUES(4244,'ABA','PE-100 Ø 110 mm','PE-100',110,1387,1.2,329);
INSERT INTO "tuberias" VALUES(4245,'ABA','FD Ø 150 mm','FD',150,6279,1.2,2074);
INSERT INTO "tuberias" VALUES(4246,'ABA','PE-100 Ø 160 mm','PE-100',160,2506,1.2,687);
INSERT INTO "tuberias" VALUES(4247,'ABA','FD Ø 200 mm','FD',200,8616,1.2,2842);
INSERT INTO "tuberias" VALUES(4248,'ABA','PE-100 Ø 200 mm','PE-100',200,3656,1.2,2842);
INSERT INTO "tuberias" VALUES(4249,'ABA','FD Ø 250 mm','FD',250,11604,1.2,3624);
INSERT INTO "tuberias" VALUES(4250,'ABA','FD Ø 300 mm','FD',300,14655,1.2,4721);
INSERT INTO "tuberias" VALUES(4251,'ABA','FD Ø 350 mm','FD',350,20098,1.2,5958);
INSERT INTO "tuberias" VALUES(4252,'ABA','FD Ø 400 mm','FD',400,23956,1.2,7026);
INSERT INTO "tuberias" VALUES(4253,'ABA','FD Ø 500 mm','FD',500,28555,1.2,9468);
INSERT INTO "tuberias" VALUES(4254,'ABA','FD Ø 600 mm','FD',600,38389,1.2,12696);
INSERT INTO "tuberias" VALUES(4255,'ABA','FD Ø 800 mm','FD',800,74971,1.2,24301);
INSERT INTO "tuberias" VALUES(4256,'ABA','FD Ø 1000 mm','FD',1000,95164,1.2,38030);
INSERT INTO "tuberias" VALUES(4257,'ABA','FD Ø 1200 mm','FD',1200,112862,1.2,65023);
INSERT INTO "tuberias" VALUES(4258,'SAN','Gres Ø 300 mm','Gres',300,12010,1.35,0);
INSERT INTO "tuberias" VALUES(4259,'SAN','HA Ø 300 mm','Hormigón',300,5439,1.0,0);
INSERT INTO "tuberias" VALUES(4260,'SAN','PVC-U Ø 315 mm','PVC',315,4373,1.2,0);
INSERT INTO "tuberias" VALUES(4261,'SAN','Gres Ø 400 mm','Gres',400,20381,1.35,0);
INSERT INTO "tuberias" VALUES(4262,'SAN','HA Ø 400 mm','Hormigón',400,5439,1.0,0);
INSERT INTO "tuberias" VALUES(4263,'SAN','PVC-U Ø 400 mm','PVC',400,8918,1.2,0);
INSERT INTO "tuberias" VALUES(4264,'SAN','Gres Ø 500 mm','Gres',500,29655,1.35,0);
INSERT INTO "tuberias" VALUES(4265,'SAN','HA Ø 500 mm','Hormigón',500,6436,1.0,0);
INSERT INTO "tuberias" VALUES(4266,'SAN','PVC-U Ø 500 mm','PVC',500,13930,1.2,0);
INSERT INTO "tuberias" VALUES(4267,'SAN','Gres Ø 600 mm','Gres',600,39276,1.35,0);
INSERT INTO "tuberias" VALUES(4268,'SAN','HA Ø 600 mm','Hormigón',600,7300,1.0,0);
INSERT INTO "tuberias" VALUES(4269,'SAN','Gres Ø 800 mm','Gres',800,97774,1.35,0);
INSERT INTO "tuberias" VALUES(4270,'SAN','HA Ø 800 mm','Hormigón',800,12839,1.0,0);
INSERT INTO "tuberias" VALUES(4271,'SAN','HA+PE80 Ø 800 mm','HA+PE80',800,50543,1.4,0);
INSERT INTO "tuberias" VALUES(4272,'SAN','Gres Ø 1000 mm','Gres',1000,121863,1.35,0);
INSERT INTO "tuberias" VALUES(4273,'SAN','HA Ø 1000 mm','Hormigón',1000,17676,1.0,0);
INSERT INTO "tuberias" VALUES(4274,'SAN','HA+PE80 Ø 1000 mm','HA+PE80',1000,54612,1.4,0);
INSERT INTO "tuberias" VALUES(4275,'SAN','HA Ø 1200 mm','Hormigón',1200,29911,1.0,0);
INSERT INTO "tuberias" VALUES(4276,'SAN','HA+PE80 Ø 1200 mm','HA+PE80',1200,73560,1.4,0);
INSERT INTO "tuberias" VALUES(4277,'SAN','HA+PE80 Ø 1500 mm','HA+PE80',1500,121388,1.4,0);
INSERT INTO "tuberias" VALUES(4278,'SAN','HA+PE80 Ø 1800 mm','HA+PE80',1800,142012,1.4,0);
INSERT INTO "tuberias" VALUES(4279,'SAN','HA+PE80 Ø 2000 mm','HA+PE80',2000,166774,1.4,0);
INSERT INTO "tuberias" VALUES(4280,'SAN','HA+PE80 Ø 2500 mm','HA+PE80',2500,247150,1.4,0);
INSERT INTO "tuberias" VALUES(4281,'SAN','HA+PE80 Ø 3000 mm','HA+PE80',3000,368036,1.4,0);
CREATE TABLE "valvuleria" (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL UNIQUE,
                tipo  TEXT NOT NULL,
                dn_min        INTEGER NOT NULL CHECK(dn_min > 0),
                dn_max        INTEGER NOT NULL CHECK(dn_max >= dn_min),
                precio        INTEGER NOT NULL CHECK(precio > 0),
                intervalo_m   REAL NOT NULL CHECK(intervalo_m > 0),
                instalacion   TEXT CHECK(instalacion IS NULL OR instalacion IN ('enterrada', 'pozo')),
                factor_piezas  REAL NOT NULL DEFAULT 1.2 CHECK(factor_piezas BETWEEN 0.5 AND 2.0),
                precio_material INTEGER NOT NULL DEFAULT 0 CHECK(precio_material >= 0)
            );
INSERT INTO "valvuleria" VALUES(3212,'Desagüe DN80 (tubería DN≤300)','desague',1,300,52224,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3213,'Conexión ɸ DN<100','conexion',1,100,72031,100.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3214,'Compuerta DN60-79','compuerta',60,79,13497,100.0,'enterrada',1.2,0);
INSERT INTO "valvuleria" VALUES(3215,'Compuerta en pozo DN60-79','compuerta',60,79,13497,100.0,'pozo',1.2,0);
INSERT INTO "valvuleria" VALUES(3216,'Pozo registro ABA','pozo_registro',60,1200,25262,100.0,'pozo',1.0,0);
INSERT INTO "valvuleria" VALUES(3217,'Tapa pozo registro ABA','tapa_pozo_registro',60,1200,18421,100.0,'pozo',1.0,15270);
INSERT INTO "valvuleria" VALUES(3218,'Ventosa trifuncional DN≤80-599','ventosa',80,599,31202,200.0,NULL,1.2,31905);
INSERT INTO "valvuleria" VALUES(3219,'Compuerta DN80-99','compuerta',80,99,14671,100.0,'enterrada',1.2,6381);
INSERT INTO "valvuleria" VALUES(3220,'Compuerta en pozo DN80-99','compuerta',80,99,14671,100.0,'pozo',1.2,6381);
INSERT INTO "valvuleria" VALUES(3221,'Pozo de desagüe','desague_pozo',80,1200,124727,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3222,'Compuerta DN100-149','compuerta',100,149,19984,100.0,'enterrada',1.2,7524);
INSERT INTO "valvuleria" VALUES(3223,'Compuerta en pozo DN100-149','compuerta',100,149,19984,100.0,'pozo',1.2,7524);
INSERT INTO "valvuleria" VALUES(3224,'Conexión ɸ DN150','conexion',101,150,185379,100.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3225,'Hidrante','hidrante',150,300,246088,200.0,NULL,1.2,258392);
INSERT INTO "valvuleria" VALUES(3226,'Compuerta DN150-199','compuerta',150,199,21621,100.0,'enterrada',1.2,11714);
INSERT INTO "valvuleria" VALUES(3227,'Compuerta en pozo DN150-199','compuerta',150,199,21621,100.0,'pozo',1.2,11714);
INSERT INTO "valvuleria" VALUES(3228,'Tapa de hidrante','tapa',150,300,16708,200.0,NULL,1.2,14543);
INSERT INTO "valvuleria" VALUES(3229,'Conexión ɸ DN200','conexion',151,200,112053,100.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3230,'Compuerta DN200-299','compuerta',200,299,27200,200.0,'enterrada',1.2,19238);
INSERT INTO "valvuleria" VALUES(3231,'Compuerta en pozo DN200-299','compuerta',200,299,27200,200.0,'pozo',1.2,19238);
INSERT INTO "valvuleria" VALUES(3232,'Conexión ɸ DN250','conexion',201,250,138683,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3233,'Conexión ɸ DN300','conexion',251,300,203846,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3234,'Compuerta DN300+','compuerta',300,1200,108839,200.0,'enterrada',1.2,48275);
INSERT INTO "valvuleria" VALUES(3235,'Compuerta en pozo DN300+','compuerta',300,1200,108839,200.0,'pozo',1.2,48275);
INSERT INTO "valvuleria" VALUES(3236,'Conexión ɸ DN400','conexion',301,400,249251,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3237,'Desagüe DN100 (tubería DN≤500)','desague',301,500,86631,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3238,'Conexión ɸ DN>400','conexion',401,9999,243266,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3239,'Desagüe DN150 (tubería DN≤800)','desague',501,800,162564,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3240,'Ventosa trifuncional DN≥600','ventosa',600,1200,77883,500.0,NULL,1.2,123810);
INSERT INTO "valvuleria" VALUES(3241,'Desagüe DN200 (tubería DN≤1000)','desague',801,1000,252571,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3242,'Desagüe DN300 (tubería DN≤1600)','desague',1001,1600,405652,200.0,NULL,1.0,0);
INSERT INTO "valvuleria" VALUES(3243,'Desagüe DN400 (tubería DN>1600)','desague',1601,9999,655941,200.0,NULL,1.0,0);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_categoria ON audit_log(categoria);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('presupuestos',116);
INSERT INTO "sqlite_sequence" VALUES('presupuesto_capitulos',247);
INSERT INTO "sqlite_sequence" VALUES('presupuesto_partidas',1189);
INSERT INTO "sqlite_sequence" VALUES('presupuesto_parametros',881);
INSERT INTO "sqlite_sequence" VALUES('presupuesto_trazabilidad',168);
INSERT INTO "sqlite_sequence" VALUES('tuberias',4281);
INSERT INTO "sqlite_sequence" VALUES('valvuleria',3243);
INSERT INTO "sqlite_sequence" VALUES('pozos',3194);
INSERT INTO "sqlite_sequence" VALUES('acerados',2100);
INSERT INTO "sqlite_sequence" VALUES('bordillos',420);
INSERT INTO "sqlite_sequence" VALUES('calzadas',525);
INSERT INTO "sqlite_sequence" VALUES('entibacion',297);
INSERT INTO "sqlite_sequence" VALUES('acometidas',945);
INSERT INTO "sqlite_sequence" VALUES('subbases',206);
INSERT INTO "sqlite_sequence" VALUES('desmontaje',306);
INSERT INTO "sqlite_sequence" VALUES('imbornales',510);
INSERT INTO "sqlite_sequence" VALUES('pozos_existentes_precios',408);
INSERT INTO "sqlite_sequence" VALUES('audit_log',2);
INSERT INTO "sqlite_sequence" VALUES('demolicion',884);
COMMIT;
