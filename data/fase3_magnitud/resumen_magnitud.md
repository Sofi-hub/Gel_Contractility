# Fase 3, tema 7 (H51): desplazamiento conocido

Pendiente = medido / verdadero (1.0 = mide bien). En blur la posicion final es s y la media s/2.

```
                    caso      variante       metodo  medido/verdadero (pendiente)  error_medio_px  error_max_abs_px  error_medio_subpixel_px
      Video_063_CTRL1_5V          blur bordes_clahe                         0.508          -0.447             1.632                   -0.233
      Video_063_CTRL1_5V          blur bordes_crudo                         0.504          -0.452             1.584                   -0.236
      Video_063_CTRL1_5V          blur  correlacion                         0.137          -0.795             2.600                   -0.429
      Video_063_CTRL1_5V        franja bordes_clahe                         1.000           0.006             0.112                    0.014
      Video_063_CTRL1_5V        franja bordes_crudo                         1.001           0.007             0.183                    0.016
      Video_063_CTRL1_5V        franja  correlacion                         0.430          -0.586             1.329                   -0.358
      Video_063_CTRL1_5V        rigido bordes_clahe                         1.001           0.007             0.110                    0.013
      Video_063_CTRL1_5V        rigido bordes_crudo                         1.001           0.007             0.183                    0.016
      Video_063_CTRL1_5V        rigido  correlacion                         0.430          -0.586             1.325                   -0.358
      Video_063_CTRL1_5V rigido_entero bordes_clahe                         0.999          -0.004             0.110                      NaN
      Video_063_CTRL1_5V rigido_entero bordes_crudo                         0.998          -0.011             0.104                      NaN
      Video_063_CTRL1_5V rigido_entero  correlacion                         0.484          -1.107             1.325                      NaN
Video_466_EXP5_FAPS4_40V          blur bordes_clahe                         0.372          -0.623             1.853                   -0.392
Video_466_EXP5_FAPS4_40V          blur bordes_crudo                         0.575          -0.384             1.572                   -0.198
Video_466_EXP5_FAPS4_40V          blur  correlacion                         0.099          -0.830             2.721                   -0.448
Video_466_EXP5_FAPS4_40V        franja bordes_clahe                         0.924          -0.115             0.544                   -0.111
Video_466_EXP5_FAPS4_40V        franja bordes_crudo                         1.019           0.032             0.277                    0.037
Video_466_EXP5_FAPS4_40V        franja  correlacion                         0.223          -0.724             2.300                   -0.395
Video_466_EXP5_FAPS4_40V        rigido bordes_clahe                         0.916          -0.120             0.461                   -0.114
Video_466_EXP5_FAPS4_40V        rigido bordes_crudo                         1.019           0.032             0.277                    0.037
Video_466_EXP5_FAPS4_40V        rigido  correlacion                         0.228          -0.721             2.270                   -0.395
Video_466_EXP5_FAPS4_40V rigido_entero bordes_clahe                         0.942          -0.125             0.434                      NaN
Video_466_EXP5_FAPS4_40V rigido_entero bordes_crudo                         1.008           0.019             0.139                      NaN
Video_466_EXP5_FAPS4_40V rigido_entero  correlacion                         0.236          -1.543             2.270                      NaN
               sintetico     analitico bordes_clahe                         0.971          -0.056             0.101                   -0.063
               sintetico     analitico bordes_crudo                         0.985          -0.033             0.064                   -0.038
               sintetico     analitico  correlacion                         0.176          -0.758             2.479                   -0.409
               sintetico rigido_interp bordes_clahe                         0.989          -0.017             0.045                   -0.017
               sintetico rigido_interp bordes_crudo                         0.998          -0.005             0.034                   -0.004
               sintetico rigido_interp  correlacion                         0.175          -0.759             2.485                   -0.409
```

## Medido por desplazamiento (mediana entre fotogramas)

```
                                            bordes_clahe  bordes_crudo  correlacion
caso                     variante      s                                           
Video_063_CTRL1_5V       blur          0.1         0.047         0.046        0.014
                                       0.2         0.096         0.094        0.028
                                       0.3         0.145         0.141        0.042
                                       0.4         0.195         0.190        0.057
                                       0.5         0.264         0.231        0.071
                                       0.6         0.317         0.288        0.085
                                       0.7         0.364         0.348        0.099
                                       0.8         0.418         0.399        0.113
                                       0.9         0.473         0.454        0.127
                                       1.0         0.530         0.499        0.141
                                       1.5         0.754         0.736        0.210
                                       2.0         1.010         1.026        0.277
                                       3.0         1.541         1.531        0.404
                         franja        0.1         0.096         0.094        0.028
                                       0.2         0.195         0.190        0.057
                                       0.3         0.311         0.304        0.085
                                       0.4         0.413         0.397        0.114
                                       0.5         0.523         0.502        0.142
                                       0.6         0.632         0.603        0.171
                                       0.7         0.710         0.708        0.199
                                       0.8         0.808         0.808        0.227
                                       0.9         0.906         0.904        0.256
                                       1.0         1.002         0.998        0.284
                                       1.5         1.512         1.500        0.423
                                       2.0         2.004         1.998        0.700
                                       3.0         3.018         2.991        1.701
                         rigido        0.1         0.096         0.094        0.028
                                       0.2         0.195         0.190        0.057
                                       0.3         0.313         0.304        0.085
                                       0.4         0.413         0.397        0.113
                                       0.5         0.523         0.502        0.142
                                       0.6         0.633         0.603        0.170
                                       0.7         0.710         0.708        0.199
                                       0.8         0.808         0.808        0.227
                                       0.9         0.904         0.904        0.256
                                       1.0         1.003         0.998        0.284
                                       1.5         1.513         1.500        0.423
                                       2.0         2.005         1.998        0.699
                                       3.0         3.018         2.991        1.698
                         rigido_entero 1.0         1.003         0.998        0.284
                                       2.0         2.005         1.998        0.699
                                       3.0         3.018         2.991        1.698
Video_466_EXP5_FAPS4_40V blur          0.1         0.008         0.051        0.011
                                       0.2        -0.081         0.091        0.021
                                       0.3         0.152         0.154        0.032
                                       0.4         0.070         0.189        0.042
                                       0.5         0.161         0.247        0.053
                                       0.6         0.212         0.303        0.063
                                       0.7         0.154         0.348        0.073
                                       0.8         0.273         0.412        0.084
                                       0.9         0.350         0.513        0.094
                                       1.0         0.373         0.634        0.104
                                       1.5         0.656         0.793        0.154
                                       2.0         0.807         1.159        0.201
                                       3.0         1.165         1.780        0.283
                         franja        0.1         0.005         0.091        0.021
                                       0.2         0.079         0.187        0.042
                                       0.3         0.161         0.296        0.063
                                       0.4         0.263         0.405        0.084
                                       0.5         0.473         0.517        0.106
                                       0.6         0.476         0.624        0.127
                                       0.7         0.616         0.731        0.148
                                       0.8         0.730         0.830        0.168
                                       0.9         0.809         0.913        0.189
                                       1.0         0.988         1.000        0.209
                                       1.5         1.483         1.517        0.306
                                       2.0         1.953         2.000        0.394
                                       3.0         2.954         3.000        0.739
                         rigido        0.1         0.005         0.091        0.021
                                       0.2         0.078         0.187        0.042
                                       0.3         0.179         0.296        0.063
                                       0.4         0.226         0.405        0.084
                                       0.5         0.482         0.517        0.105
                                       0.6         0.466         0.624        0.126
                                       0.7         0.598         0.731        0.147
                                       0.8         0.699         0.830        0.168
                                       0.9         0.813         0.913        0.189
                                       1.0         0.994         1.000        0.210
                                       1.5         1.459         1.517        0.308
                                       2.0         1.961         2.000        0.396
                                       3.0         2.914         3.000        0.758
                         rigido_entero 1.0         0.994         1.000        0.210
                                       2.0         1.961         2.000        0.396
                                       3.0         2.914         3.000        0.758
sintetico                analitico     0.1         0.076         0.078        0.018
                                       0.2         0.166         0.177        0.037
                                       0.3         0.243         0.263        0.055
                                       0.4         0.341         0.364        0.073
                                       0.5         0.440         0.483        0.091
                                       0.6         0.540         0.574        0.109
                                       0.7         0.599         0.645        0.127
                                       0.8         0.699         0.736        0.145
                                       0.9         0.827         0.842        0.163
                                       1.0         0.940         0.948        0.181
                                       1.5         1.477         1.473        0.269
                                       2.0         1.908         1.946        0.352
                                       3.0         3.017         3.037        0.521
                         rigido_interp 0.1         0.091         0.106        0.018
                                       0.2         0.180         0.197        0.036
                                       0.3         0.294         0.295        0.055
                                       0.4         0.382         0.399        0.073
                                       0.5         0.496         0.478        0.091
                                       0.6         0.555         0.566        0.109
                                       0.7         0.679         0.696        0.127
                                       0.8         0.776         0.803        0.145
                                       0.9         0.893         0.926        0.163
                                       1.0         0.974         1.000        0.180
                                       1.5         1.473         1.478        0.268
                                       2.0         2.004         2.000        0.352
                                       3.0         2.980         3.000        0.515
```
