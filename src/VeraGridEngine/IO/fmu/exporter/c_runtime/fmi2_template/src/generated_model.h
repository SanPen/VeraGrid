#ifndef GENERATED_MODEL_H
#define GENERATED_MODEL_H

#include "model_instance.h"

double vg_heaviside(double x);
double vg_safe_log(double x);
double vg_safe_sqrt(double x);

void generated_set_start_values(ModelInstance* instance);
void generated_eval_init(ModelInstance* instance);
void generated_eval_discrete_init(ModelInstance* instance);
void generated_eval_residual(ModelInstance* instance, double* out);
void generated_eval_outputs(ModelInstance* instance);
double generated_procedural_next_event(ModelInstance* instance, double t_prev, double t_target);
void generated_procedural_update(ModelInstance* instance, double t);
int generated_get_real(ModelInstance* instance, fmi2ValueReference vr, double* value);
int generated_set_real(ModelInstance* instance, fmi2ValueReference vr, double value);

#endif
