# Fase 3, tema 6: medicion de borde y ajuste

max_frames = todos, paso_denso = 10

## F en sinteticos
```
[
 {
  "caso": "sintetico plana 150 px (verdadera 885-1035)",
  "metodo_auto": "gauge_rescate_plana",
  "roi_auto": "0-553",
  "var_auto_pct": 5.82,
  "cintura_px": 437.8,
  "minimo_perfil_en_ok_px": 283.0,
  "alternativas": [
   [
    "gauge_plana",
    923,
    998,
    0.0
   ],
   [
    "gauge_cintura",
    644,
    1277,
    62.19
   ],
   [
    "gauge_relajada",
    630,
    1291,
    69.96
   ],
   [
    "solo_nitidez",
    0,
    1920,
    131.45
   ],
   [
    "franja_completa",
    0,
    1920,
    131.45
   ],
   [
    "gauge_rescate_plana",
    0,
    553,
    5.82
   ]
  ],
  "roi_auto_contiene_cintura": false,
  "roi_auto_grosor_min_sobre_cintura_pct": 41.39,
  "rescate_actual_min180": "0-553",
  "rescate_con_cintura_min180": "813-1108",
  "rescate_actual_min150": "0-553",
  "rescate_con_cintura_min150": "813-1108",
  "rescate_actual_min120": "0-553",
  "rescate_con_cintura_min120": "813-1108"
 },
 {
  "caso": "sintetico plana 300 px (verdadera 810-1110)",
  "metodo_auto": "gauge_plana",
  "roi_auto": "848-1073",
  "var_auto_pct": 0.0,
  "cintura_px": 403.0,
  "minimo_perfil_en_ok_px": 283.0,
  "alternativas": [
   [
    "gauge_plana",
    848,
    1073,
    0.0
   ],
   [
    "gauge_cintura",
    595,
    1326,
    49.47
   ],
   [
    "gauge_relajada",
    580,
    1341,
    56.54
   ],
   [
    "solo_nitidez",
    0,
    1920,
    131.45
   ],
   [
    "franja_completa",
    0,
    1920,
    131.45
   ]
  ],
  "roi_auto_contiene_cintura": true,
  "roi_auto_grosor_min_sobre_cintura_pct": -29.78,
  "rescate_actual_min180": "0-478",
  "rescate_con_cintura_min180": "738-1183",
  "rescate_actual_min150": "0-478",
  "rescate_con_cintura_min150": "738-1183",
  "rescate_actual_min120": "0-478",
  "rescate_con_cintura_min120": "738-1183"
 },
 {
  "caso": "sintetico plana 1000 px (verdadera 460-1460)",
  "metodo_auto": "gauge_plana",
  "roi_auto": "498-1423",
  "var_auto_pct": 0.0,
  "cintura_px": 283.0,
  "minimo_perfil_en_ok_px": 283.0,
  "alternativas": [
   [
    "gauge_plana",
    498,
    1423,
    0.0
   ],
   [
    "gauge_cintura",
    392,
    1529,
    4.95
   ],
   [
    "gauge_relajada",
    364,
    1557,
    9.89
   ],
   [
    "solo_nitidez",
    0,
    1920,
    131.45
   ],
   [
    "franja_completa",
    0,
    1920,
    131.45
   ]
  ],
  "roi_auto_contiene_cintura": true,
  "roi_auto_grosor_min_sobre_cintura_pct": 0.0,
  "rescate_actual_min180": "388-1533",
  "rescate_con_cintura_min180": "388-1533",
  "rescate_actual_min150": "388-1533",
  "rescate_con_cintura_min150": "388-1533",
  "rescate_actual_min120": "388-1533",
  "rescate_con_cintura_min120": "388-1533"
 }
]
```

## Video_prueba

```
 variante  n_eventos  k_usado       meseta                 mesetas  reportable  amplitud_px  ruido_canal_px  ruido_grosor_px  ruido_fotograma_centro_px  ruido_fotograma_grosor_px  outlier_frac_medio  periodo_s  periodo_err_s  cociente_robusto_pct  amplitud_relativa_pct  ttp_s  rt50_s
  vigente         29    9.415 5.315-15.163 29 ev en k=5.315-15.163        True       2.0937        0.085398         0.090060                   0.301388                   0.105008            0.035894   10.00043         0.0023             18.166984               2.314267    NaN     NaN
clahe_mco         29   10.357  6.431-16.68  29 ev en k=6.431-16.68        True       2.1146        0.074130         0.067800                   0.301835                   0.092686            0.000000   10.00026         0.0023             17.003962               2.352101    NaN     NaN
    crudo         29    8.559 5.315-12.532 29 ev en k=5.315-12.532        True       2.0266        0.091476         0.086248                   0.284536                   0.214181            0.032171   10.00030         0.0023              8.618700               2.334231    NaN     NaN
crudo_mco         29   10.357 7.074-15.163 29 ev en k=7.074-15.163        True       2.0411        0.076354         0.060876                   0.285229                   0.196528            0.000000   10.00019         0.0023              9.384925               2.347740    NaN     NaN
ventana25         29    9.415 5.315-15.163 29 ev en k=5.315-15.163        True       2.0937        0.085546         0.089284                   0.301350                   0.104551            0.036114   10.00043         0.0023             18.166984               2.314267    NaN     NaN
```

```
{
 "video": "Video_prueba",
 "n_frames": 2007,
 "roi": "454-1516",
 "segundos_proceso": 370.0,
 "control_max_dif_center_px": 0.0,
 "control_max_dif_thickness_px": 1.7053025658242404e-13,
 "eventos_vs_vigente": {
  "clahe_mco": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "crudo": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "crudo_mco": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "ventana25": {
   "nuevos_s": [],
   "perdidos_s": []
  }
 },
 "B_clahe_menos_crudo": {
  "center_px": {
   "ruido_dif_px": 0.05367011999992759,
   "desvio_dif_total_px": 0.08344639015785563,
   "excursion_en_eventos_px": [
    0.168,
    0.084,
    -0.063,
    0.112,
    0.063,
    -0.144,
    0.107,
    0.175,
    0.2,
    0.096,
    0.066,
    -0.142,
    -0.107,
    0.13,
    0.075,
    0.106,
    0.114,
    -0.088,
    0.122,
    1.055,
    0.074,
    0.087,
    0.029,
    0.1,
    1.188,
    1.208,
    1.234,
    1.051,
    0.844
   ],
   "excursion_mediana_en_ruidos": 2.0830957709833218,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.05370569280343716,
   "corr_con_senal": 0.3606547314405596
  },
  "thickness_px": {
   "ruido_dif_px": 0.1094044844427853,
   "desvio_dif_total_px": 0.2216451478067223,
   "excursion_en_eventos_px": [
    -0.294,
    -0.269,
    -0.619,
    -0.52,
    -0.308,
    -0.279,
    -0.325,
    -0.311,
    -0.412,
    -0.349,
    -0.248,
    -0.17,
    0.23,
    -0.387,
    -0.322,
    -0.167,
    -0.362,
    -0.292,
    -0.431,
    -3.2,
    -0.13,
    -0.26,
    0.184,
    -0.21,
    -3.601,
    -3.104,
    -3.468,
    -3.217,
    -2.621
   ],
   "excursion_mediana_en_ruidos": 2.9429922240214816,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": -0.6161493078466174
  },
  "y_top_px": {
   "ruido_dif_px": 0.08628732000008332,
   "desvio_dif_total_px": 0.18074815008142261,
   "excursion_en_eventos_px": [
    0.278,
    0.212,
    0.341,
    0.393,
    0.21,
    0.13,
    0.219,
    0.289,
    0.378,
    0.273,
    0.191,
    0.108,
    -0.256,
    0.312,
    0.242,
    0.138,
    0.279,
    0.207,
    0.299,
    2.669,
    0.128,
    0.221,
    -0.104,
    0.144,
    2.985,
    2.772,
    2.972,
    2.668,
    2.188
   ],
   "excursion_mediana_en_ruidos": 3.1638484078507028,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.546433625650851
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.0584144400000008,
   "desvio_dif_total_px": 0.07986461878695102,
   "excursion_en_eventos_px": [
    -0.139,
    0.04,
    -0.178,
    -0.164,
    -0.072,
    -0.223,
    -0.118,
    0.218,
    -0.151,
    -0.099,
    -0.149,
    -0.179,
    -0.12,
    -0.133,
    -0.129,
    -0.181,
    -0.185,
    -0.112,
    -0.158,
    -0.534,
    -0.14,
    -0.175,
    0.125,
    -0.158,
    -0.624,
    -0.412,
    -0.487,
    -0.554,
    -0.48
   ],
   "excursion_mediana_en_ruidos": 2.703098754347807,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.21482277121374865,
   "corr_con_senal": -0.4756895189936786
  },
  "media_dif_px": {
   "y_top_px": 0.4921572496263082,
   "y_bottom_px": -0.37938420528151523
  }
 },
 "C_ransac_menos_mco": {
  "center_px": {
   "ruido_dif_px": 0.036471960000030876,
   "desvio_dif_total_px": 0.04151880738124882,
   "excursion_en_eventos_px": [
    0.073,
    0.091,
    -0.031,
    0.05,
    -0.027,
    -0.094,
    0.072,
    0.114,
    0.062,
    0.034,
    -0.09,
    -0.08,
    -0.057,
    -0.057,
    0.05,
    -0.049,
    -0.066,
    0.05,
    0.075,
    -0.128,
    -0.027,
    0.054,
    -0.045,
    0.039,
    -0.061,
    -0.095,
    -0.171,
    -0.101,
    -0.134
   ],
   "excursion_mediana_en_ruidos": 1.688968731045614,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": -0.05502577163682649
  },
  "thickness_px": {
   "ruido_dif_px": 0.07026852791380991,
   "desvio_dif_total_px": 0.07239074606983098,
   "excursion_en_eventos_px": [
    -0.117,
    -0.12,
    -0.074,
    -0.114,
    0.046,
    0.054,
    -0.132,
    -0.099,
    -0.19,
    0.072,
    -0.142,
    0.07,
    0.139,
    -0.109,
    -0.149,
    0.093,
    -0.099,
    -0.107,
    -0.164,
    0.187,
    -0.115,
    -0.14,
    0.142,
    -0.203,
    -0.156,
    -0.101,
    0.244,
    -0.156,
    -0.156
   ],
   "excursion_mediana_en_ruidos": 1.708513486053237,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": -0.056854761540881524
  },
  "y_top_px": {
   "ruido_dif_px": 0.06597569999995685,
   "desvio_dif_total_px": 0.06602981098784912,
   "excursion_en_eventos_px": [
    0.119,
    0.118,
    0.052,
    0.101,
    -0.049,
    -0.057,
    0.13,
    0.103,
    -0.103,
    -0.048,
    0.095,
    -0.086,
    -0.117,
    0.1,
    0.104,
    -0.033,
    0.096,
    0.099,
    0.094,
    -0.228,
    0.052,
    0.092,
    -0.1,
    0.156,
    0.079,
    -0.115,
    -0.302,
    -0.125,
    -0.157
   ],
   "excursion_mediana_en_ruidos": 1.5096467335703563,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": -0.009548915464384581
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.0
  },
  "media_dif_px": {
   "y_top_px": -0.012178126557050079,
   "y_bottom_px": -0.0050961634280012325
  }
 },
 "C_columnas": {
  "superior": {
   "primeras10": {
    "descartadas_pct": 0.7,
    "residuo_mediano_px": 0.612
   },
   "centro": {
    "descartadas_pct": 8.3,
    "residuo_mediano_px": 0.541
   },
   "ultimas10": {
    "descartadas_pct": 1.8,
    "residuo_mediano_px": 0.62
   }
  },
  "inferior": {
   "primeras10": {
    "descartadas_pct": 5.3,
    "residuo_mediano_px": 0.627
   },
   "centro": {
    "descartadas_pct": 0.5,
    "residuo_mediano_px": 0.553
   },
   "ultimas10": {
    "descartadas_pct": 0.0,
    "residuo_mediano_px": 0.456
   }
  }
 },
 "C_columnas_descartadas_mas_50pct": {
  "superior": [
   17,
   18,
   37
  ],
  "inferior": []
 },
 "D_bordes_nan_pct": {
  "clahe15": 0.0,
  "crudo15": 0.0,
  "clahe25": 0.001
 },
 "D_max_dif_ventana25_vs_15": {
  "center_px": 0.0986000000000331,
  "thickness_px": 0.20511862029417216
 },
 "E_separacion_columnas_px": 17.98,
 "E_ruido_compartido": {
  "clahe_superior": {
   "r_a_1px": 0.301,
   "r_a_3px": 0.143,
   "r_a_la_separacion_actual": 0.005,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "clahe_inferior": {
   "r_a_1px": 0.598,
   "r_a_3px": 0.372,
   "r_a_la_separacion_actual": -0.003,
   "distancia_r_bajo_0.5_px": 2,
   "distancia_r_bajo_0.2_px": 8
  },
  "crudo_superior": {
   "r_a_1px": 0.419,
   "r_a_3px": 0.156,
   "r_a_la_separacion_actual": 0.014,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 3
  },
  "crudo_inferior": {
   "r_a_1px": 0.584,
   "r_a_3px": 0.3,
   "r_a_la_separacion_actual": 0.01,
   "distancia_r_bajo_0.5_px": 2,
   "distancia_r_bajo_0.2_px": 5
  }
 },
 "F_rescate": {
  "caso": "Video_prueba",
  "metodo_auto": "gauge_cintura",
  "roi_auto": "454-1516",
  "var_auto_pct": 5.32,
  "cintura_px": 302.0,
  "minimo_perfil_en_ok_px": 301.0,
  "alternativas": [
   [
    "gauge_plana",
    862,
    955,
    0.33
   ],
   [
    "gauge_cintura",
    454,
    1516,
    5.32
   ],
   [
    "gauge_relajada",
    362,
    1642,
    10.3
   ],
   [
    "solo_nitidez",
    362,
    1820,
    27.91
   ],
   [
    "franja_completa",
    0,
    1870,
    402.08
   ]
  ],
  "roi_auto_contiene_cintura": true,
  "roi_auto_grosor_min_sobre_cintura_pct": -0.33,
  "rescate_actual_min180": "425-1527",
  "rescate_con_cintura_min180": "425-1527",
  "rescate_actual_min150": "425-1527",
  "rescate_con_cintura_min150": "425-1527",
  "rescate_actual_min120": "425-1527",
  "rescate_con_cintura_min120": "425-1527"
 }
}
```

## Video_063_CTRL1_5V

```
 variante  n_eventos  k_usado       meseta                                       mesetas  reportable  amplitud_px  ruido_canal_px  ruido_grosor_px  ruido_fotograma_centro_px  ruido_fotograma_grosor_px  outlier_frac_medio  periodo_s  periodo_err_s  cociente_robusto_pct  amplitud_relativa_pct  ttp_s  rt50_s
  vigente          6    6.431  5.315-8.559 6 ev en k=5.315-8.559; 5 ev en k=9.415-24.421        True       1.5135        0.034322         0.065366                   0.061602                   0.048738            0.077329   10.00190        0.00304             12.824673               0.535484    NaN     NaN
clahe_mco          5   10.357 4.832-20.182                        5 ev en k=4.832-20.182        True       1.4083        0.058563         0.112007                   0.061220                   0.058711            0.001433   10.00012        0.00304             10.486559               0.492957    NaN     NaN
    crudo          5   11.392 4.832-24.421                        5 ev en k=4.832-24.421       False       1.4825        0.051001         0.100713                   0.062758                   0.058394            0.076721   10.00276        0.00304             16.434937               0.516735    NaN     NaN
crudo_mco          5    9.415 4.392-18.348                        5 ev en k=4.392-18.348        True       1.3925        0.066124         0.103733                   0.063870                   0.065754            0.000683    9.99910        0.00304              8.006674               0.486245    NaN     NaN
ventana25          5   13.785 7.781-24.421                        5 ev en k=7.781-24.421        True       1.5668        0.033210         0.063236                   0.062694                   0.047441            0.085155   10.00000        0.00304             10.917986               0.547308    NaN     NaN
```

```
{
 "video": "Video_063_CTRL1_5V",
 "n_frames": 1848,
 "roi": "390-1423",
 "segundos_proceso": 303.0,
 "control_max_dif_center_px": 0.0,
 "control_max_dif_thickness_px": 1.7053025658242404e-13,
 "eventos_vs_vigente": {
  "clahe_mco": {
   "nuevos_s": [],
   "perdidos_s": [
    0.308
   ]
  },
  "crudo": {
   "nuevos_s": [],
   "perdidos_s": [
    0.308
   ]
  },
  "crudo_mco": {
   "nuevos_s": [],
   "perdidos_s": [
    0.308
   ]
  },
  "ventana25": {
   "nuevos_s": [],
   "perdidos_s": [
    0.308
   ]
  }
 },
 "B_clahe_menos_crudo": {
  "center_px": {
   "ruido_dif_px": 0.036768479999956444,
   "desvio_dif_total_px": 0.04820662960184476,
   "excursion_en_eventos_px": [
    0.066,
    0.055,
    -0.058,
    -0.103,
    0.097,
    0.142
   ],
   "excursion_mediana_en_ruidos": 2.217932315942223,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.5500550055005501,
   "corr_con_senal": 0.19260333208295988
  },
  "thickness_px": {
   "ruido_dif_px": 0.07659546085564997,
   "desvio_dif_total_px": 0.09682898009059007,
   "excursion_en_eventos_px": [
    0.18,
    -0.031,
    -0.091,
    -0.264,
    -0.142,
    -0.135
   ],
   "excursion_mediana_en_ruidos": 1.8065122484595733,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.385038503850385,
   "corr_con_senal": 0.08179003769118028
  },
  "y_top_px": {
   "ruido_dif_px": 0.03120873000000364,
   "desvio_dif_total_px": 0.041068087485661445,
   "excursion_en_eventos_px": [
    0.08,
    0.051,
    -0.072,
    0.052,
    0.073,
    0.15
   ],
   "excursion_mediana_en_ruidos": 2.3262721680755916,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.7150715071507151,
   "corr_con_senal": 0.1213842381923421
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.0639741899999536,
   "desvio_dif_total_px": 0.08682924456784037,
   "excursion_en_eventos_px": [
    0.136,
    0.04,
    -0.101,
    -0.264,
    0.135,
    0.178
   ],
   "excursion_mediana_en_ruidos": 2.1211679272540334,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 1.1001100110011002,
   "corr_con_senal": 0.1394351853966511
  },
  "media_dif_px": {
   "y_top_px": 0.42545952380952307,
   "y_bottom_px": -0.2245884199134202
  }
 },
 "C_ransac_menos_mco": {
  "center_px": {
   "ruido_dif_px": 0.07086827999999284,
   "desvio_dif_total_px": 0.09011204495150496,
   "excursion_en_eventos_px": [
    0.157,
    0.222,
    -0.123,
    0.124,
    0.112,
    -0.135
   ],
   "excursion_mediana_en_ruidos": 1.8259226836038436,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.2190151064985916
  },
  "thickness_px": {
   "ruido_dif_px": 0.15001699390663092,
   "desvio_dif_total_px": 0.16798846979270973,
   "excursion_en_eventos_px": [
    -0.138,
    -0.425,
    -0.169,
    -0.325,
    0.199,
    0.208
   ],
   "excursion_mediana_en_ruidos": 1.3541833296537624,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.06025647585061574
  },
  "y_top_px": {
   "ruido_dif_px": 0.06330701999999468,
   "desvio_dif_total_px": 0.12844413778105793,
   "excursion_en_eventos_px": [
    0.197,
    0.373,
    0.227,
    0.169,
    -0.089,
    -0.084
   ],
   "excursion_mediana_en_ruidos": 2.8914644852973614,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 2.255225522552255,
   "corr_con_senal": 0.10721702458448155
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.09844464000006553,
   "desvio_dif_total_px": 0.11742451980196045,
   "excursion_en_eventos_px": [
    0.095,
    0.14,
    -0.127,
    -0.125,
    0.176,
    -0.199
   ],
   "excursion_mediana_en_ruidos": 1.3576158133123644,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.2001159665350026
  },
  "media_dif_px": {
   "y_top_px": -0.5369553030303036,
   "y_bottom_px": 0.006261201298701354
  }
 },
 "C_columnas": {
  "superior": {
   "primeras10": {
    "descartadas_pct": 6.6,
    "residuo_mediano_px": 0.972
   },
   "centro": {
    "descartadas_pct": 6.3,
    "residuo_mediano_px": 0.86
   },
   "ultimas10": {
    "descartadas_pct": 10.3,
    "residuo_mediano_px": 1.738
   }
  },
  "inferior": {
   "primeras10": {
    "descartadas_pct": 16.3,
    "residuo_mediano_px": 0.559
   },
   "centro": {
    "descartadas_pct": 5.1,
    "residuo_mediano_px": 0.528
   },
   "ultimas10": {
    "descartadas_pct": 14.0,
    "residuo_mediano_px": 1.002
   }
  }
 },
 "C_columnas_descartadas_mas_50pct": {
  "superior": [
   41,
   47,
   59
  ],
  "inferior": [
   0,
   1,
   44,
   50
  ]
 },
 "D_bordes_nan_pct": {
  "clahe15": 0.144,
  "crudo15": 0.069,
  "clahe25": 0.091
 },
 "D_max_dif_ventana25_vs_15": {
  "center_px": 0.12229999999999563,
  "thickness_px": 0.2373704764577269
 },
 "E_separacion_columnas_px": 17.49,
 "E_ruido_compartido": {
  "clahe_superior": {
   "r_a_1px": 0.066,
   "r_a_3px": -0.002,
   "r_a_la_separacion_actual": -0.011,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 1
  },
  "clahe_inferior": {
   "r_a_1px": 0.11,
   "r_a_3px": -0.033,
   "r_a_la_separacion_actual": -0.001,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 1
  },
  "crudo_superior": {
   "r_a_1px": 0.044,
   "r_a_3px": 0.018,
   "r_a_la_separacion_actual": -0.01,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 1
  },
  "crudo_inferior": {
   "r_a_1px": 0.011,
   "r_a_3px": 0.001,
   "r_a_la_separacion_actual": -0.005,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 1
  }
 },
 "F_rescate": {
  "caso": "Video_063_CTRL1_5V",
  "metodo_auto": "gauge_cintura",
  "roi_auto": "390-1423",
  "var_auto_pct": 4.91,
  "cintura_px": 285.0,
  "minimo_perfil_en_ok_px": 285.0,
  "alternativas": [
   [
    "gauge_plana",
    875,
    1039,
    0.35
   ],
   [
    "gauge_cintura",
    390,
    1423,
    4.91
   ],
   [
    "gauge_relajada",
    184,
    1553,
    9.82
   ],
   [
    "solo_nitidez",
    135,
    1568,
    12.63
   ],
   [
    "franja_completa",
    0,
    1920,
    682.81
   ]
  ],
  "roi_auto_contiene_cintura": true,
  "roi_auto_grosor_min_sobre_cintura_pct": 0.0,
  "rescate_actual_min180": "313-1447",
  "rescate_con_cintura_min180": "313-1447",
  "rescate_actual_min150": "313-1447",
  "rescate_con_cintura_min150": "313-1447",
  "rescate_actual_min120": "313-1447",
  "rescate_con_cintura_min120": "313-1447"
 }
}
```

## Video_268_EXP3_FAPS2_40V

```
 variante  n_eventos  k_usado       meseta                mesetas  reportable  amplitud_px  ruido_canal_px  ruido_grosor_px  ruido_fotograma_centro_px  ruido_fotograma_grosor_px  outlier_frac_medio  periodo_s  periodo_err_s  cociente_robusto_pct  amplitud_relativa_pct  ttp_s  rt50_s
  vigente          6   12.532 5.846-24.421 6 ev en k=5.846-24.421        True      1.54685        0.049371         0.070406                   0.058617                   0.044783            0.020143   10.00132         0.0023             -2.401975               0.574945    NaN     NaN
clahe_mco          6   10.357 4.832-22.201 6 ev en k=4.832-22.201        True      1.52505        0.057970         0.102702                   0.061507                   0.061230            0.000004    9.99996         0.0023             -5.522752               0.566874    NaN     NaN
    crudo          6   10.357  5.846-16.68  6 ev en k=5.846-16.68        True      1.48635        0.076947         0.133134                   0.071256                   0.094036            0.045110   10.00019         0.0023              6.295119               0.550256    NaN     NaN
crudo_mco          6   12.532 6.431-24.421 6 ev en k=6.431-24.421        True      1.46245        0.053670         0.097510                   0.058970                   0.053572            0.000000    9.99968         0.0023              6.749603               0.541475    NaN     NaN
ventana25          6   12.532 5.846-24.421 6 ev en k=5.846-24.421        True      1.54505        0.048629         0.071431                   0.058737                   0.045167            0.019639   10.00114         0.0023             -2.219393               0.574266    NaN     NaN
```

```
{
 "video": "Video_268_EXP3_FAPS2_40V",
 "n_frames": 2283,
 "roi": "918-1328",
 "segundos_proceso": 315.3,
 "control_max_dif_center_px": 0.0,
 "control_max_dif_thickness_px": 1.1368683772161603e-13,
 "eventos_vs_vigente": {
  "clahe_mco": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "crudo": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "crudo_mco": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "ventana25": {
   "nuevos_s": [],
   "perdidos_s": []
  }
 },
 "B_clahe_menos_crudo": {
  "center_px": {
   "ruido_dif_px": 0.08910425999996616,
   "desvio_dif_total_px": 0.11822602911643496,
   "excursion_en_eventos_px": [
    0.099,
    0.12,
    0.125,
    0.172,
    -0.232,
    0.135
   ],
   "excursion_mediana_en_ruidos": 1.4600873179357328,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.3994673768308922,
   "corr_con_senal": 0.18640509766484203
  },
  "thickness_px": {
   "ruido_dif_px": 0.1493187724156222,
   "desvio_dif_total_px": 0.2298174271778525,
   "excursion_en_eventos_px": [
    0.188,
    0.269,
    0.231,
    0.339,
    0.697,
    -0.23
   ],
   "excursion_mediana_en_ruidos": 1.6737162624459578,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.5326231691078562,
   "corr_con_senal": -0.03675953697927287
  },
  "y_top_px": {
   "ruido_dif_px": 0.13788180000002628,
   "desvio_dif_total_px": 0.22488774162103656,
   "excursion_en_eventos_px": [
    -0.093,
    -0.185,
    -0.197,
    -0.295,
    -0.574,
    -0.099
   ],
   "excursion_mediana_en_ruidos": 1.3863323513324952,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 1.5534842432312472,
   "corr_con_senal": 0.11059227022060349
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.04596059999992449,
   "desvio_dif_total_px": 0.0615470219483804,
   "excursion_en_eventos_px": [
    0.106,
    0.188,
    0.182,
    0.25,
    0.356,
    -0.183
   ],
   "excursion_mediana_en_ruidos": 4.0404172269344905,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.6657789613848202,
   "corr_con_senal": 0.29035664288499335
  },
  "media_dif_px": {
   "y_top_px": 0.5510759964958389,
   "y_bottom_px": -0.3991126587823035
  }
 },
 "C_ransac_menos_mco": {
  "center_px": {
   "ruido_dif_px": 0.03454458000000903,
   "desvio_dif_total_px": 0.05112262457140673,
   "excursion_en_eventos_px": [
    -0.064,
    -0.125,
    0.116,
    0.092,
    -0.066,
    -0.15
   ],
   "excursion_mediana_en_ruidos": 3.0048129113149216,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.7545494895694629,
   "corr_con_senal": 0.0971444268776383
  },
  "thickness_px": {
   "ruido_dif_px": 0.09094565590031985,
   "desvio_dif_total_px": 0.10095372730520755,
   "excursion_en_eventos_px": [
    0.236,
    0.202,
    -0.267,
    -0.184,
    0.116,
    -0.256
   ],
   "excursion_mediana_en_ruidos": 2.4117593503134467,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": -0.05962126488608629
  },
  "y_top_px": {
   "ruido_dif_px": 0.0756125999999818,
   "desvio_dif_total_px": 0.09915939466851179,
   "excursion_en_eventos_px": [
    -0.128,
    -0.226,
    0.265,
    0.184,
    -0.122,
    0.22
   ],
   "excursion_mediana_en_ruidos": 2.6721736853382354,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.07639074152056861
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.006375180000085219,
   "desvio_dif_total_px": 0.020993830526061137,
   "excursion_en_eventos_px": [
    0.107,
    0.045,
    -0.054,
    -0.031,
    0.034,
    -0.106
   ],
   "excursion_mediana_en_ruidos": 7.764486649679642,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 10.430537061695517,
   "corr_con_senal": 0.09513255416019846
  },
  "media_dif_px": {
   "y_top_px": -0.006298247919404312,
   "y_bottom_px": -0.008425711782742113
  }
 },
 "C_columnas": {
  "superior": {
   "primeras10": {
    "descartadas_pct": 0.4,
    "residuo_mediano_px": 0.72
   },
   "centro": {
    "descartadas_pct": 1.6,
    "residuo_mediano_px": 0.534
   },
   "ultimas10": {
    "descartadas_pct": 0.9,
    "residuo_mediano_px": 0.61
   }
  },
  "inferior": {
   "primeras10": {
    "descartadas_pct": 1.2,
    "residuo_mediano_px": 0.437
   },
   "centro": {
    "descartadas_pct": 1.9,
    "residuo_mediano_px": 0.607
   },
   "ultimas10": {
    "descartadas_pct": 7.3,
    "residuo_mediano_px": 0.392
   }
  }
 },
 "C_columnas_descartadas_mas_50pct": {
  "superior": [
   36
  ],
  "inferior": [
   48,
   57
  ]
 },
 "D_bordes_nan_pct": {
  "clahe15": 0.0,
  "crudo15": 0.0,
  "clahe25": 0.108
 },
 "D_max_dif_ventana25_vs_15": {
  "center_px": 0.04670000000004393,
  "thickness_px": 0.09338893973620088
 },
 "E_separacion_columnas_px": 6.93,
 "E_ruido_compartido": {
  "clahe_superior": {
   "r_a_1px": 0.265,
   "r_a_3px": 0.005,
   "r_a_la_separacion_actual": 0.019,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "clahe_inferior": {
   "r_a_1px": 0.263,
   "r_a_3px": 0.076,
   "r_a_la_separacion_actual": 0.017,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "crudo_superior": {
   "r_a_1px": 0.282,
   "r_a_3px": 0.088,
   "r_a_la_separacion_actual": 0.008,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "crudo_inferior": {
   "r_a_1px": 0.457,
   "r_a_3px": 0.128,
   "r_a_la_separacion_actual": 0.034,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 3
  }
 },
 "F_rescate": {
  "caso": "Video_268_EXP3_FAPS2_40V",
  "metodo_auto": "gauge_cintura",
  "roi_auto": "918-1328",
  "var_auto_pct": 5.24,
  "cintura_px": 268.0,
  "minimo_perfil_en_ok_px": 267.0,
  "alternativas": [
   [
    "gauge_plana",
    918,
    998,
    0.75
   ],
   [
    "gauge_cintura",
    918,
    1328,
    5.24
   ],
   [
    "gauge_relajada",
    477,
    917,
    10.11
   ],
   [
    "solo_nitidez",
    396,
    917,
    13.11
   ],
   [
    "franja_completa",
    126,
    1875,
    8775.0
   ]
  ],
  "roi_auto_contiene_cintura": true,
  "roi_auto_grosor_min_sobre_cintura_pct": -0.37,
  "rescate_actual_min180": "918-1336",
  "rescate_con_cintura_min180": "918-1336",
  "rescate_actual_min150": "918-1336",
  "rescate_con_cintura_min150": "918-1336",
  "rescate_actual_min120": "918-1336",
  "rescate_con_cintura_min120": "918-1336"
 }
}
```

## Video_466_EXP5_FAPS4_40V

```
 variante  n_eventos  k_usado       meseta                mesetas  reportable  amplitud_px  ruido_canal_px  ruido_grosor_px  ruido_fotograma_centro_px  ruido_fotograma_grosor_px  outlier_frac_medio  periodo_s  periodo_err_s  cociente_robusto_pct  amplitud_relativa_pct    ttp_s   rt50_s
  vigente          5    8.559  3.993-16.68  5 ev en k=3.993-16.68        True       4.2936        0.211641         0.364992                   0.136961                   0.216651            0.079496   10.00224        0.00693              6.267959               2.134093 0.284271 0.160404
clahe_mco          5   11.392 5.315-22.201 5 ev en k=5.315-22.201        True       4.1090        0.167015         0.280078                   0.115829                   0.147630            0.009644   10.00351        0.00304             -1.189834               2.043414 0.216238 0.193324
    crudo          5    9.415 4.392-20.182 5 ev en k=4.392-20.182        True       4.3402        0.202375         0.236358                   0.127293                   0.151153            0.099025    9.99930        0.00304             -0.382285               2.150742 0.254556 0.167026
crudo_mco          5   12.532 5.846-24.421 5 ev en k=5.846-24.421        True       4.0399        0.105932         0.106076                   0.087798                   0.062872            0.000716   10.00297        0.00304              1.232147               1.992116 0.259975 0.191505
ventana25          0    8.559         None                   None       False          NaN        1.096753         2.258623                   0.686269                   1.401561            0.119718        NaN            NaN                   NaN                    NaN      NaN      NaN
```

```
{
 "video": "Video_466_EXP5_FAPS4_40V",
 "n_frames": 2076,
 "roi": "700-900",
 "segundos_proceso": 314.1,
 "control_max_dif_center_px": 0.0,
 "control_max_dif_thickness_px": 1.1368683772161603e-13,
 "eventos_vs_vigente": {
  "clahe_mco": {
   "nuevos_s": [
    54.177
   ],
   "perdidos_s": [
    54.322
   ]
  },
  "crudo": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "crudo_mco": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "ventana25": {
   "nuevos_s": [],
   "perdidos_s": [
    14.312,
    24.32,
    34.277,
    44.243,
    54.322
   ]
  }
 },
 "B_clahe_menos_crudo": {
  "center_px": {
   "ruido_dif_px": 0.23795730000001955,
   "desvio_dif_total_px": 0.27385417297227865,
   "excursion_en_eventos_px": [
    -0.417,
    -0.762,
    -0.459,
    0.375,
    0.466
   ],
   "excursion_mediana_en_ruidos": 1.9293377425277443,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.14627011214041932,
   "corr_con_senal": 0.12181339484719118
  },
  "thickness_px": {
   "ruido_dif_px": 0.4617498466947638,
   "desvio_dif_total_px": 0.5214748000266143,
   "excursion_en_eventos_px": [
    -1.989,
    -1.848,
    -1.23,
    -1.693,
    -0.871
   ],
   "excursion_mediana_en_ruidos": 3.666649368335329,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.09751340809361286,
   "corr_con_senal": -0.31560139323223396
  },
  "y_top_px": {
   "ruido_dif_px": 0.27027797999999686,
   "desvio_dif_total_px": 0.34025572144598215,
   "excursion_en_eventos_px": [
    0.684,
    0.313,
    0.415,
    1.159,
    0.44
   ],
   "excursion_mediana_en_ruidos": 1.6268435926597546,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.24378352023403219,
   "corr_con_senal": 0.2819884895670019
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.35841855000003636,
   "desvio_dif_total_px": 0.4406496579940494,
   "excursion_en_eventos_px": [
    -1.321,
    -1.69,
    -1.172,
    -0.563,
    -0.751
   ],
   "excursion_mediana_en_ruidos": 3.2707570520553273,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.19502681618722573,
   "corr_con_senal": -0.06599949574783257
  },
  "media_dif_px": {
   "y_top_px": 0.12643607899807252,
   "y_bottom_px": -0.5760482177263956
  }
 },
 "C_ransac_menos_mco": {
  "center_px": {
   "ruido_dif_px": 0.2023749000000182,
   "desvio_dif_total_px": 0.2306767402929283,
   "excursion_en_eventos_px": [
    0.23,
    -0.053,
    0.18,
    0.529,
    0.271
   ],
   "excursion_mediana_en_ruidos": 1.134528046709272,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.04875670404680643,
   "corr_con_senal": 0.2651272695148171
  },
  "thickness_px": {
   "ruido_dif_px": 0.33087532473844744,
   "desvio_dif_total_px": 0.425737070252302,
   "excursion_en_eventos_px": [
    -0.79,
    -0.766,
    -0.704,
    -1.494,
    -0.902
   ],
   "excursion_mediana_en_ruidos": 2.3884374663574253,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.14627011214041932,
   "corr_con_senal": -0.2955383534946064
  },
  "y_top_px": {
   "ruido_dif_px": 0.24855788999997114,
   "desvio_dif_total_px": 0.3037038980537883,
   "excursion_en_eventos_px": [
    0.517,
    0.277,
    0.276,
    0.854,
    0.571
   ],
   "excursion_mediana_en_ruidos": 2.08080298718364,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.09751340809361286,
   "corr_con_senal": 0.36926881773892367
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.3228361499998665,
   "desvio_dif_total_px": 0.3529577982926463,
   "excursion_en_eventos_px": [
    -0.368,
    -0.469,
    -0.578,
    -0.793,
    -0.173
   ],
   "excursion_mediana_en_ruidos": 1.4518200641415355,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.03039279724240968
  },
  "media_dif_px": {
   "y_top_px": -0.42321912331406597,
   "y_bottom_px": -0.37662943159922796
  }
 },
 "C_columnas": {
  "superior": {
   "primeras10": {
    "descartadas_pct": 16.0,
    "residuo_mediano_px": 2.162
   },
   "centro": {
    "descartadas_pct": 6.9,
    "residuo_mediano_px": 1.339
   },
   "ultimas10": {
    "descartadas_pct": 1.9,
    "residuo_mediano_px": 1.245
   }
  },
  "inferior": {
   "primeras10": {
    "descartadas_pct": 10.5,
    "residuo_mediano_px": 0.495
   },
   "centro": {
    "descartadas_pct": 9.6,
    "residuo_mediano_px": 0.761
   },
   "ultimas10": {
    "descartadas_pct": 1.1,
    "residuo_mediano_px": 0.474
   }
  }
 },
 "C_columnas_descartadas_mas_50pct": {
  "superior": [
   7,
   8,
   19,
   22
  ],
  "inferior": []
 },
 "D_bordes_nan_pct": {
  "clahe15": 0.965,
  "crudo15": 0.072,
  "clahe25": 3.679
 },
 "D_max_dif_ventana25_vs_15": {
  "center_px": 10.173299999999983,
  "thickness_px": 20.04378125105609
 },
 "E_separacion_columnas_px": 3.37,
 "E_ruido_compartido": {
  "clahe_superior": {
   "r_a_1px": 0.442,
   "r_a_3px": 0.094,
   "r_a_la_separacion_actual": 0.094,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "clahe_inferior": {
   "r_a_1px": 0.412,
   "r_a_3px": 0.125,
   "r_a_la_separacion_actual": 0.125,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "crudo_superior": {
   "r_a_1px": 0.469,
   "r_a_3px": 0.138,
   "r_a_la_separacion_actual": 0.138,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 3
  },
  "crudo_inferior": {
   "r_a_1px": 0.32,
   "r_a_3px": 0.057,
   "r_a_la_separacion_actual": 0.057,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  }
 },
 "F_rescate": {
  "caso": "Video_466_EXP5_FAPS4_40V",
  "metodo_auto": "gauge_rescate_plana",
  "roi_auto": "944-1169",
  "var_auto_pct": 5.77,
  "cintura_px": 206.0,
  "minimo_perfil_en_ok_px": 201.0,
  "alternativas": [
   [
    "gauge_plana",
    796,
    816,
    1.44
   ],
   [
    "gauge_cintura",
    696,
    846,
    4.85
   ],
   [
    "gauge_relajada",
    877,
    1177,
    12.44
   ],
   [
    "solo_nitidez",
    1302,
    1817,
    40.57
   ],
   [
    "franja_completa",
    71,
    1920,
    164.63
   ],
   [
    "gauge_rescate_plana",
    944,
    1169,
    5.77
   ]
  ],
  "roi_auto_contiene_cintura": true,
  "roi_auto_grosor_min_sobre_cintura_pct": 0.97,
  "rescate_actual_min180": "944-1169",
  "rescate_con_cintura_min180": "944-1169",
  "rescate_actual_min150": "944-1169",
  "rescate_con_cintura_min150": "944-1169",
  "rescate_actual_min120": "944-1169",
  "rescate_con_cintura_min120": "944-1169"
 }
}
```

## Video_583_EXP6_CTRL4_40V

```
 variante  n_eventos  k_usado        meseta                 mesetas  reportable  amplitud_px  ruido_canal_px  ruido_grosor_px  ruido_fotograma_centro_px  ruido_fotograma_grosor_px  outlier_frac_medio  periodo_s  periodo_err_s  cociente_robusto_pct  amplitud_relativa_pct    ttp_s   rt50_s
  vigente          6   16.680 12.532-24.421 6 ev en k=12.532-24.421        True      3.09545        0.072499         0.116531                   0.105525                   0.093044            0.040001   10.00024         0.0023              0.972820               1.309524 0.257811 0.181028
clahe_mco          6   15.163  9.415-24.421  6 ev en k=9.415-24.421        True      2.99370        0.085398         0.157975                   0.103149                   0.104949            0.005535   10.00000         0.0023             -6.483377               1.268848 0.258587 0.177249
    crudo         15    8.559          None                    None       False      0.65690        0.039585         0.055064                   0.105171                   0.074337            0.023262   10.00011         0.0023             -2.163469               1.321364      NaN      NaN
crudo_mco         18    8.559          None                    None       False      0.56160        0.036324         0.053040                   0.102928                   0.073126            0.000817   10.00004         0.0023             -3.038062               1.322943      NaN      NaN
ventana25          6   16.680 11.392-24.421 6 ev en k=11.392-24.421        True      3.08920        0.073463         0.120003                   0.105011                   0.091928            0.035842   10.00027         0.0023              1.135769               1.306846 0.257800 0.179370
```

```
{
 "video": "Video_583_EXP6_CTRL4_40V",
 "n_frames": 2236,
 "roi": "718-1187",
 "segundos_proceso": 338.2,
 "control_max_dif_center_px": 0.0,
 "control_max_dif_thickness_px": 1.1368683772161603e-13,
 "eventos_vs_vigente": {
  "clahe_mco": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "crudo": {
   "nuevos_s": [
    71.987,
    72.187,
    72.287,
    72.387,
    72.487,
    72.588,
    72.688,
    73.287,
    73.387
   ],
   "perdidos_s": []
  },
  "crudo_mco": {
   "nuevos_s": [
    3.822,
    71.987,
    72.187,
    72.287,
    72.387,
    72.487,
    72.588,
    72.722,
    73.287,
    73.387,
    73.528,
    73.687
   ],
   "perdidos_s": []
  },
  "ventana25": {
   "nuevos_s": [],
   "perdidos_s": []
  }
 },
 "B_clahe_menos_crudo": {
  "center_px": {
   "ruido_dif_px": 0.055152719999976806,
   "desvio_dif_total_px": 0.07314572770340523,
   "excursion_en_eventos_px": [
    -0.098,
    -0.092,
    -0.116,
    -0.046,
    -0.072,
    -0.075
   ],
   "excursion_mediana_en_ruidos": 1.5194173560258095,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.271985494106981,
   "corr_con_senal": 0.009764947093561717
  },
  "thickness_px": {
   "ruido_dif_px": 0.11616389995174678,
   "desvio_dif_total_px": 0.14291153842815826,
   "excursion_en_eventos_px": [
    -0.191,
    -0.347,
    0.192,
    -0.216,
    0.067,
    0.181
   ],
   "excursion_mediana_en_ruidos": 1.6507784951317135,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.3173164097914778,
   "corr_con_senal": -0.08569443063921346
  },
  "y_top_px": {
   "ruido_dif_px": 0.09911180999998233,
   "desvio_dif_total_px": 0.10982316088743377,
   "excursion_en_eventos_px": [
    -0.093,
    0.294,
    -0.142,
    0.127,
    -0.025,
    -0.165
   ],
   "excursion_mediana_en_ruidos": 1.3575576916617118,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.271985494106981,
   "corr_con_senal": 0.06281348092598768
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.07012698000009465,
   "desvio_dif_total_px": 0.1028093467223866,
   "excursion_en_eventos_px": [
    -0.179,
    -0.18,
    -0.199,
    -0.143,
    -0.12,
    -0.023
   ],
   "excursion_mediana_en_ruidos": 2.294409369971576,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.40797824116047143,
   "corr_con_senal": -0.06724393857100766
  },
  "media_dif_px": {
   "y_top_px": 0.9114649821109122,
   "y_bottom_px": -0.6496928443649389
  }
 },
 "C_ransac_menos_mco": {
  "center_px": {
   "ruido_dif_px": 0.07079415000009573,
   "desvio_dif_total_px": 0.07823695129925118,
   "excursion_en_eventos_px": [
    0.197,
    0.168,
    0.079,
    0.071,
    0.06,
    0.181
   ],
   "excursion_mediana_en_ruidos": 1.7473195172158196,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.22554483102516032
  },
  "thickness_px": {
   "ruido_dif_px": 0.14906320702040382,
   "desvio_dif_total_px": 0.16028019866295296,
   "excursion_en_eventos_px": [
    -0.442,
    -0.384,
    -0.171,
    -0.148,
    -0.097,
    -0.353
   ],
   "excursion_mediana_en_ruidos": 1.7558046854623213,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": -0.21710659051753484
  },
  "y_top_px": {
   "ruido_dif_px": 0.1420330799999534,
   "desvio_dif_total_px": 0.15598343164911352,
   "excursion_en_eventos_px": [
    0.393,
    0.336,
    0.159,
    0.141,
    0.12,
    0.362
   ],
   "excursion_mediana_en_ruidos": 1.7414957135344291,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.21719826393087574
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.0
  },
  "media_dif_px": {
   "y_top_px": -0.40328568872987425,
   "y_bottom_px": 0.00040174418604643807
  }
 },
 "C_columnas": {
  "superior": {
   "primeras10": {
    "descartadas_pct": 0.7,
    "residuo_mediano_px": 0.537
   },
   "centro": {
    "descartadas_pct": 9.2,
    "residuo_mediano_px": 0.883
   },
   "ultimas10": {
    "descartadas_pct": 10.3,
    "residuo_mediano_px": 1.339
   }
  },
  "inferior": {
   "primeras10": {
    "descartadas_pct": 0.0,
    "residuo_mediano_px": 0.747
   },
   "centro": {
    "descartadas_pct": 0.0,
    "residuo_mediano_px": 1.088
   },
   "ultimas10": {
    "descartadas_pct": 0.1,
    "residuo_mediano_px": 1.059
   }
  }
 },
 "C_columnas_descartadas_mas_50pct": {
  "superior": [
   27,
   35,
   48
  ],
  "inferior": []
 },
 "D_bordes_nan_pct": {
  "clahe15": 0.555,
  "crudo15": 0.082,
  "clahe25": 0.013
 },
 "D_max_dif_ventana25_vs_15": {
  "center_px": 0.151299999999992,
  "thickness_px": 0.30940891987916075
 },
 "E_separacion_columnas_px": 7.93,
 "E_ruido_compartido": {
  "clahe_superior": {
   "r_a_1px": 0.329,
   "r_a_3px": 0.057,
   "r_a_la_separacion_actual": -0.009,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "clahe_inferior": {
   "r_a_1px": 0.519,
   "r_a_3px": 0.178,
   "r_a_la_separacion_actual": 0.005,
   "distancia_r_bajo_0.5_px": 2,
   "distancia_r_bajo_0.2_px": 3
  },
  "crudo_superior": {
   "r_a_1px": 0.207,
   "r_a_3px": 0.081,
   "r_a_la_separacion_actual": 0.01,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "crudo_inferior": {
   "r_a_1px": 0.435,
   "r_a_3px": 0.17,
   "r_a_la_separacion_actual": 0.005,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 3
  }
 },
 "F_rescate": {
  "caso": "Video_583_EXP6_CTRL4_40V",
  "metodo_auto": "gauge_cintura",
  "roi_auto": "718-1187",
  "var_auto_pct": 5.83,
  "cintura_px": 242.0,
  "minimo_perfil_en_ok_px": 240.0,
  "alternativas": [
   [
    "gauge_plana",
    923,
    964,
    0.83
   ],
   [
    "gauge_cintura",
    718,
    1187,
    5.83
   ],
   [
    "gauge_relajada",
    634,
    1296,
    10.83
   ],
   [
    "solo_nitidez",
    345,
    1296,
    26.67
   ],
   [
    "franja_completa",
    0,
    1881,
    285.42
   ]
  ],
  "roi_auto_contiene_cintura": true,
  "roi_auto_grosor_min_sobre_cintura_pct": -0.83,
  "rescate_actual_min180": "718-1187",
  "rescate_con_cintura_min180": "718-1187",
  "rescate_actual_min150": "718-1187",
  "rescate_con_cintura_min150": "718-1187",
  "rescate_actual_min120": "718-1187",
  "rescate_con_cintura_min120": "718-1187"
 }
}
```

## Video_491_EXP5_CTRL1_36HZ

```
 variante  n_eventos  k_usado        meseta                 mesetas  reportable  amplitud_px  ruido_canal_px  ruido_grosor_px  ruido_fotograma_centro_px  ruido_fotograma_grosor_px  outlier_frac_medio periodo_s periodo_err_s  cociente_robusto_pct  amplitud_relativa_pct    ttp_s   rt50_s
  vigente          2   10.357  7.781-13.785  2 ev en k=7.781-13.785        True      1.01520        0.067977         0.102678                   0.041183                   0.065601            0.041982      None          None             -5.552551               0.397456 0.569836 0.466520
clahe_mco          2   10.357  7.781-13.785  2 ev en k=7.781-13.785        True      0.98715        0.067532         0.128038                   0.039956                   0.060480            0.005436      None          None             -5.752147               0.386181 0.571599 0.467806
    crudo          2   12.532   9.415-16.68   2 ev en k=9.415-16.68        True      1.07495        0.059007         0.078725                   0.040570                   0.052656            0.053068      None          None             -3.062207               0.419207 0.567355 0.466551
crudo_mco          2   15.163 11.392-20.182 2 ev en k=11.392-20.182        True      0.99780        0.047443         0.042564                   0.035961                   0.026075            0.000940      None          None             -0.944063               0.388774 0.503963 0.533958
ventana25          2   10.357  8.559-13.785  2 ev en k=8.559-13.785        True      1.00625        0.068719         0.109869                   0.041482                   0.065967            0.044279      None          None             -4.731670               0.393973 0.570063 0.467047
```

```
{
 "video": "Video_491_EXP5_CTRL1_36HZ",
 "n_frames": 1846,
 "roi": "459-1206",
 "segundos_proceso": 277.9,
 "control_max_dif_center_px": 0.0,
 "control_max_dif_thickness_px": 1.4210854715202004e-13,
 "eventos_vs_vigente": {
  "clahe_mco": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "crudo": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "crudo_mco": {
   "nuevos_s": [],
   "perdidos_s": []
  },
  "ventana25": {
   "nuevos_s": [],
   "perdidos_s": []
  }
 },
 "B_clahe_menos_crudo": {
  "center_px": {
   "ruido_dif_px": 0.04492278000001645,
   "desvio_dif_total_px": 0.05433334325169141,
   "excursion_en_eventos_px": [
    0.046,
    0.049
   ],
   "excursion_mediana_en_ruidos": 1.0573700024809929,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.0,
   "corr_con_senal": 0.19562256098072747
  },
  "thickness_px": {
   "ruido_dif_px": 0.11069805783120697,
   "desvio_dif_total_px": 0.1468187838235577,
   "excursion_en_eventos_px": [
    -0.047,
    0.168
   ],
   "excursion_mediana_en_ruidos": 0.9729898244408547,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.5991285403050108,
   "corr_con_senal": -0.2499458518434238
  },
  "y_top_px": {
   "ruido_dif_px": 0.0786519299999352,
   "desvio_dif_total_px": 0.10102986019179401,
   "excursion_en_eventos_px": [
    0.074,
    -0.107
   ],
   "excursion_mediana_en_ruidos": 1.1493678540382002,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.32679738562091504,
   "corr_con_senal": 0.25846228941051846
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.043810830000042746,
   "desvio_dif_total_px": 0.05615939791749388,
   "excursion_en_eventos_px": [
    0.064,
    0.043
   ],
   "excursion_mediana_en_ruidos": 1.218876702403457,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.7625272331154684,
   "corr_con_senal": -0.09245657302974541
  },
  "media_dif_px": {
   "y_top_px": 0.5860899241603462,
   "y_bottom_px": -0.3106436619718326
  }
 },
 "C_ransac_menos_mco": {
  "center_px": {
   "ruido_dif_px": 0.030245039999908442,
   "desvio_dif_total_px": 0.03926931696136596,
   "excursion_en_eventos_px": [
    -0.026,
    -0.033
   ],
   "excursion_mediana_en_ruidos": 0.9654475576852071,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.8714596949891068,
   "corr_con_senal": 0.21694658615318071
  },
  "thickness_px": {
   "ruido_dif_px": 0.097440522448427,
   "desvio_dif_total_px": 0.11854045007499064,
   "excursion_en_eventos_px": [
    0.09,
    -0.06
   ],
   "excursion_mediana_en_ruidos": 0.7666164538258178,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.16339869281045752,
   "corr_con_senal": -0.09038189103699226
  },
  "y_top_px": {
   "ruido_dif_px": 0.05841443999995867,
   "desvio_dif_total_px": 0.07379327350020203,
   "excursion_en_eventos_px": [
    -0.075,
    -0.039
   ],
   "excursion_mediana_en_ruidos": 0.9809218405592598,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 0.3812636165577342,
   "corr_con_senal": 0.19989364413106425
  },
  "y_bottom_px": {
   "ruido_dif_px": 0.016753380000092636,
   "desvio_dif_total_px": 0.02605847251592032,
   "excursion_en_eventos_px": [
    0.003,
    -0.028
   ],
   "excursion_mediana_en_ruidos": 0.9222019675970853,
   "frac_fotogramas_fuera_de_eventos_sobre_4ruidos_pct": 2.342047930283224,
   "corr_con_senal": 0.10576367017556097
  },
  "media_dif_px": {
   "y_top_px": -0.007405850487540813,
   "y_bottom_px": -0.045817334777898774
  }
 },
 "C_columnas": {
  "superior": {
   "primeras10": {
    "descartadas_pct": 0.6,
    "residuo_mediano_px": 0.449
   },
   "centro": {
    "descartadas_pct": 5.0,
    "residuo_mediano_px": 0.705
   },
   "ultimas10": {
    "descartadas_pct": 13.7,
    "residuo_mediano_px": 0.95
   }
  },
  "inferior": {
   "primeras10": {
    "descartadas_pct": 5.7,
    "residuo_mediano_px": 0.708
   },
   "centro": {
    "descartadas_pct": 2.6,
    "residuo_mediano_px": 0.8
   },
   "ultimas10": {
    "descartadas_pct": 0.2,
    "residuo_mediano_px": 0.523
   }
  }
 },
 "C_columnas_descartadas_mas_50pct": {
  "superior": [
   47,
   49,
   54
  ],
  "inferior": [
   20
  ]
 },
 "D_bordes_nan_pct": {
  "clahe15": 0.545,
  "crudo15": 0.094,
  "clahe25": 0.027
 },
 "D_max_dif_ventana25_vs_15": {
  "center_px": 0.18299999999999272,
  "thickness_px": 0.5413779359830357
 },
 "E_separacion_columnas_px": 12.64,
 "E_ruido_compartido": {
  "clahe_superior": {
   "r_a_1px": 0.376,
   "r_a_3px": 0.084,
   "r_a_la_separacion_actual": -0.006,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "clahe_inferior": {
   "r_a_1px": 0.436,
   "r_a_3px": 0.17,
   "r_a_la_separacion_actual": -0.019,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 3
  },
  "crudo_superior": {
   "r_a_1px": 0.238,
   "r_a_3px": 0.071,
   "r_a_la_separacion_actual": -0.001,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  },
  "crudo_inferior": {
   "r_a_1px": 0.402,
   "r_a_3px": 0.15,
   "r_a_la_separacion_actual": -0.006,
   "distancia_r_bajo_0.5_px": 1,
   "distancia_r_bajo_0.2_px": 2
  }
 },
 "F_rescate": {
  "caso": "Video_491_EXP5_CTRL1_36HZ",
  "metodo_auto": "gauge_cintura",
  "roi_auto": "459-1206",
  "var_auto_pct": 5.08,
  "cintura_px": 257.0,
  "minimo_perfil_en_ok_px": 256.0,
  "alternativas": [
   [
    "gauge_plana",
    661,
    739,
    1.17
   ],
   [
    "gauge_cintura",
    459,
    1206,
    5.08
   ],
   [
    "gauge_relajada",
    234,
    1206,
    10.16
   ],
   [
    "solo_nitidez",
    106,
    1206,
    15.62
   ],
   [
    "franja_completa",
    0,
    1920,
    360.44
   ]
  ],
  "roi_auto_contiene_cintura": true,
  "roi_auto_grosor_min_sobre_cintura_pct": -0.39,
  "rescate_actual_min180": "420-1206",
  "rescate_con_cintura_min180": "420-1206",
  "rescate_actual_min150": "420-1206",
  "rescate_con_cintura_min150": "420-1206",
  "rescate_actual_min120": "420-1206",
  "rescate_con_cintura_min120": "420-1206"
 }
}
```
