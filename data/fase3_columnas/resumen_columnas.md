# H19: cantidad de columnas y ROI automatica de 466

La primera fila de cada video es la referencia (en Video_prueba y 063, la vigente; en 466, la manual vigente): `control_max_dif_center_vs_vigente` tiene que dar ~0.

## Video_prueba

```
                                                         0                        1                                                 2                        3                        4
config                                         vigente_n60              vigente_n50                                       vigente_n40              vigente_n30              vigente_n20
roi                                               454-1516                 454-1516                                          454-1516                 454-1516                 454-1516
ancho_px                                              1062                     1062                                              1062                     1062                     1062
n_col                                                   60                       50                                                40                       30                       20
separacion_px                                        17.98                    21.65                                             27.21                    36.59                    55.84
n_eventos                                               29                       29                                                29                       29                       29
reportable                                            True                     True                                              True                     True                     True
mesetas                            29 ev en k=5.315-15.163  29 ev en k=5.315-12.532  29 ev en k=5.315-11.392; 28 ev en k=12.532-16.68  29 ev en k=4.832-11.392  29 ev en k=4.392-10.357
amplitud_px                                         2.0937                   2.0821                                            2.0504                   2.0972                   2.0862
amplitud_rel_pct                                  2.314267                 2.309249                                          2.300935                 2.340894                 2.356895
ruido_canal_px                                    0.085398                 0.093552                                          0.096369                 0.106895                 0.111047
ruido_grosor_px                                    0.09006                 0.064161                                          0.122946                 0.127964                 0.106908
ruido_fotog_centro_px                             0.301388                 0.300511                                          0.298749                 0.304544                 0.305468
outlier_frac_medio                                0.035894                 0.052162                                          0.038173                 0.056659                 0.033296
residuo_sup_px                                      0.7715                   0.6028                                            0.8518                   0.6496                   0.7177
residuo_inf_px                                      0.7972                   0.9862                                            0.9832                   0.9502                   0.8567
fotogramas_rechazados                                    0                        0                                                 0                        0                        0
periodo_s                                         10.00043                 10.00018                                          10.00021                 10.00033                 10.00032
ttp_s                                                  NaN                      NaN                                               NaN                      NaN                      NaN
rt50_s                                                 NaN                      NaN                                               NaN                      NaN                      NaN
control_max_dif_center_vs_vigente                      0.0                      NaN                                               NaN                      NaN                      NaN
ruido_canal / referencia                               1.0                    1.095                                             1.128                    1.252                      1.3
prediccion_independiente                               1.0                    1.095                                             1.225                    1.414                    1.732
```

Eventos (s):
```
vigente_n60: [np.float64(0.34), np.float64(0.91), np.float64(1.47), np.float64(2.04), np.float64(2.6), np.float64(3.17), np.float64(3.74), np.float64(4.31), np.float64(4.87), np.float64(5.45), np.float64(5.97), np.float64(6.57), np.float64(7.28), np.float64(7.67), np.float64(8.28), np.float64(9.34), np.float64(9.94), np.float64(10.54), np.float64(11.67), np.float64(14.94), np.float64(15.28), np.float64(15.55), np.float64(15.84), np.float64(16.3), np.float64(24.94), np.float64(34.94), np.float64(44.94), np.float64(54.94), np.float64(64.94)]
vigente_n50: [np.float64(0.34), np.float64(0.94), np.float64(1.47), np.float64(2.04), np.float64(2.6), np.float64(3.17), np.float64(3.74), np.float64(4.31), np.float64(4.87), np.float64(5.45), np.float64(5.97), np.float64(6.57), np.float64(7.28), np.float64(7.67), np.float64(8.28), np.float64(9.34), np.float64(9.94), np.float64(10.54), np.float64(11.67), np.float64(14.94), np.float64(15.28), np.float64(15.55), np.float64(15.84), np.float64(16.3), np.float64(24.94), np.float64(34.94), np.float64(44.94), np.float64(54.94), np.float64(64.94)]
vigente_n40: [np.float64(0.34), np.float64(0.91), np.float64(1.47), np.float64(2.04), np.float64(2.6), np.float64(3.17), np.float64(3.78), np.float64(4.31), np.float64(4.87), np.float64(5.45), np.float64(5.97), np.float64(6.57), np.float64(7.28), np.float64(7.67), np.float64(8.28), np.float64(9.34), np.float64(9.94), np.float64(10.54), np.float64(11.67), np.float64(14.94), np.float64(15.28), np.float64(15.55), np.float64(15.84), np.float64(16.3), np.float64(24.94), np.float64(34.94), np.float64(44.94), np.float64(54.94), np.float64(64.94)]
vigente_n30: [np.float64(0.34), np.float64(0.91), np.float64(1.47), np.float64(2.04), np.float64(2.6), np.float64(3.2), np.float64(3.74), np.float64(4.31), np.float64(4.87), np.float64(5.45), np.float64(5.97), np.float64(6.57), np.float64(7.28), np.float64(7.67), np.float64(8.28), np.float64(9.34), np.float64(9.94), np.float64(10.54), np.float64(11.67), np.float64(14.94), np.float64(15.28), np.float64(15.55), np.float64(15.84), np.float64(16.3), np.float64(24.94), np.float64(34.94), np.float64(44.94), np.float64(54.94), np.float64(64.94)]
vigente_n20: [np.float64(0.34), np.float64(0.94), np.float64(1.47), np.float64(2.04), np.float64(2.6), np.float64(3.17), np.float64(3.74), np.float64(4.31), np.float64(4.87), np.float64(5.45), np.float64(5.97), np.float64(6.57), np.float64(7.28), np.float64(7.67), np.float64(8.28), np.float64(9.34), np.float64(9.94), np.float64(10.54), np.float64(11.67), np.float64(14.94), np.float64(15.28), np.float64(15.55), np.float64(15.84), np.float64(16.3), np.float64(24.94), np.float64(34.94), np.float64(44.94), np.float64(54.94), np.float64(64.94)]
```

## Video_063_CTRL1_5V

```
                                                                               0                       1                       2                         3                         4
config                                                               vigente_n60             vigente_n50             vigente_n40               vigente_n30               vigente_n20
roi                                                                     390-1423                390-1423                390-1423                  390-1423                  390-1423
ancho_px                                                                    1033                    1033                    1033                      1033                      1033
n_col                                                                         60                      50                      40                        30                        20
separacion_px                                                              17.49                   21.06                   26.46                     35.59                     54.32
n_eventos                                                                      6                       5                       5                        10                        14
reportable                                                                  True                   False                    True                      True                      True
mesetas                            6 ev en k=5.315-8.559; 5 ev en k=9.415-24.421  5 ev en k=7.074-24.421  5 ev en k=5.315-24.421  10 ev en k=12.532-18.348  14 ev en k=12.532-18.348
amplitud_px                                                               1.5135                   1.519                  1.5068                   0.98705                   0.93635
amplitud_rel_pct                                                        0.535484                0.530451                0.526598                  0.522075                  0.535695
ruido_canal_px                                                          0.034322                0.032098                0.048481                  0.035212                  0.036472
ruido_grosor_px                                                         0.065366                0.060886                0.084805                  0.070607                  0.065824
ruido_fotog_centro_px                                                   0.061602                0.061887                0.062998                  0.076061                  0.088005
outlier_frac_medio                                                      0.077329                 0.07086                0.064867                  0.083531                  0.111621
residuo_sup_px                                                           0.87975                 0.78385                 0.85385                    0.8654                    0.7628
residuo_inf_px                                                            0.7818                 0.73975                 0.80455                   0.76405                    0.4131
fotogramas_rechazados                                                          0                       0                       0                         0                         0
periodo_s                                                                10.0019                 9.99842                 9.99747                   9.99929                    9.9996
ttp_s                                                                        NaN                     NaN                     NaN                       NaN                       NaN
rt50_s                                                                       NaN                     NaN                     NaN                       NaN                       NaN
control_max_dif_center_vs_vigente                                            0.0                     NaN                     NaN                       NaN                       NaN
ruido_canal / referencia                                                     1.0                   0.935                   1.413                     1.026                     1.063
prediccion_independiente                                                     1.0                   1.095                   1.225                     1.414                     1.732
```

Eventos (s):
```
vigente_n60: [np.float64(0.31), np.float64(11.91), np.float64(21.91), np.float64(31.91), np.float64(41.91), np.float64(51.91)]
vigente_n50: [np.float64(11.91), np.float64(21.91), np.float64(31.91), np.float64(41.91), np.float64(51.91)]
vigente_n40: [np.float64(11.91), np.float64(21.91), np.float64(31.91), np.float64(41.91), np.float64(51.91)]
vigente_n30: [np.float64(1.85), np.float64(1.94), np.float64(11.91), np.float64(21.91), np.float64(31.12), np.float64(31.91), np.float64(33.81), np.float64(34.11), np.float64(41.91), np.float64(51.91)]
vigente_n20: [np.float64(3.48), np.float64(3.55), np.float64(3.61), np.float64(3.78), np.float64(11.91), np.float64(21.91), np.float64(31.91), np.float64(41.41), np.float64(41.91), np.float64(51.91), np.float64(55.39), np.float64(57.28), np.float64(59.15), np.float64(59.28)]
```

## Video_466_EXP5_FAPS4_40V

```
                                                       0                       1                       2                       3                       4
config                                    manual_vigente          rescate_actual             cintura_n50             cintura_n40             cintura_n30
roi                                              700-900                944-1169                 696-846                 696-846                 696-846
ancho_px                                             200                     225                     150                     150                     150
n_col                                                 60                      60                      50                      40                      30
separacion_px                                       3.37                     3.8                    3.04                    3.82                    5.14
n_eventos                                              5                       5                       5                       5                       5
reportable                                          True                    True                    True                    True                    True
mesetas                            5 ev en k=3.993-16.68  5 ev en k=7.074-18.348  5 ev en k=6.431-20.182  5 ev en k=4.832-24.421  5 ev en k=4.832-20.182
amplitud_px                                       4.2936                  4.0263                  4.3582                  4.4612                  4.4083
amplitud_rel_pct                                2.134093                1.971477                2.164354                2.214666                2.187563
ruido_canal_px                                  0.211641                0.192071                0.182434                0.159898                0.185992
ruido_grosor_px                                 0.364992                0.234426                0.282674                0.235799                0.256413
ruido_fotog_centro_px                           0.136961                0.132147                 0.13594                0.121793                0.129871
outlier_frac_medio                              0.079496                0.161677                0.104952                  0.1023                0.091979
residuo_sup_px                                    1.7465                 0.81755                 1.31955                   1.348                 1.33735
residuo_inf_px                                   0.68085                  0.7214                 0.58515                  0.5799                 0.59085
fotogramas_rechazados                                  0                       0                       0                       0                       0
periodo_s                                       10.00224                10.00236                10.00184                10.00308                10.00262
ttp_s                                           0.284271                0.221087                0.254989                0.293565                0.281737
rt50_s                                          0.160404                0.189712                0.192037                     NaN                0.161071
control_max_dif_center_vs_vigente                    0.0                     NaN                     NaN                     NaN                     NaN
ruido_canal / referencia                             1.0                   0.908                   0.862                   0.756                   0.879
prediccion_independiente                             1.0                     1.0                   1.095                   1.225                   1.414
```

Eventos (s):
```
manual_vigente: [np.float64(14.31), np.float64(24.32), np.float64(34.28), np.float64(44.24), np.float64(54.32)]
rescate_actual: [np.float64(14.31), np.float64(24.24), np.float64(34.21), np.float64(44.24), np.float64(54.34)]
cintura_n50: [np.float64(14.24), np.float64(24.32), np.float64(34.28), np.float64(44.34), np.float64(54.28)]
cintura_n40: [np.float64(14.34), np.float64(24.32), np.float64(34.31), np.float64(44.31), np.float64(54.32)]
cintura_n30: [np.float64(14.18), np.float64(24.28), np.float64(34.31), np.float64(44.34), np.float64(54.32)]
```
