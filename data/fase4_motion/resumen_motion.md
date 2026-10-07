# Fase 4, punto 2: motion_check viejo vs arreglado

Autoprueba:
```
 verdad_px  viejo_px  nuevo_px
      0.25     0.025     0.250
      0.50     0.051     0.499
      1.00     0.101     0.997
      2.00     0.201     1.997
      3.00     0.298     2.997
```

```
                                           0                   1                         2
video                           Video_prueba  Video_063_CTRL1_5V  Video_466_EXP5_FAPS4_40V
fotogramas                              2007                1848                      2076
n_eventos                                 29                   6                         5
pendiente_todo_viejo                   0.414                0.46                     0.231
correlacion_viejo                      0.914               0.967                      0.93
pendiente_eventos_viejo                0.419               0.484                      0.28
cociente_mediano_eventos_viejo         0.182               0.523                      0.29
frac_sin_enganche_viejo_pct              0.0                 0.0                       0.0
pendiente_todo_nuevo                    0.96               0.935                     0.847
correlacion_nuevo                      0.996               0.974                     0.959
pendiente_eventos_nuevo                0.962               0.981                     0.892
cociente_mediano_eventos_nuevo         0.963               0.987                     0.875
frac_sin_enganche_nuevo_pct              0.0                 0.0                       0.0
ruido_center_px                        0.085               0.024                     0.182
ruido_desp_nuevo_px                    0.065               0.011                     0.097
```
