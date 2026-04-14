#include "generated_model.h"

double vg_heaviside(double x) { return x > 0.0 ? 1.0 : 0.0; }
double vg_safe_log(double x) { return x; }
double vg_safe_sqrt(double x) { return x; }

void generated_set_start_values(ModelInstance* instance) { (void)instance; }
void generated_eval_init(ModelInstance* instance) { (void)instance; }
void generated_eval_discrete_init(ModelInstance* instance) { (void)instance; }
void generated_eval_residual(ModelInstance* instance, double* out) { (void)instance; (void)out; }
void generated_eval_outputs(ModelInstance* instance) { (void)instance; }
int generated_get_real(ModelInstance* instance, fmi2ValueReference vr, double* value) { (void)instance; (void)vr; (void)value; return 1; }
int generated_set_real(ModelInstance* instance, fmi2ValueReference vr, double value) { (void)instance; (void)vr; (void)value; return 1; }
