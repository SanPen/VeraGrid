#ifndef RUNTIME_SUPPORT_H
#define RUNTIME_SUPPORT_H

#include "../include/fmi2Functions.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifndef NAN
#define NAN (0.0 / 0.0)
#endif

#ifndef isnan
#define isnan(x) ((x) != (x))
#endif

#endif
