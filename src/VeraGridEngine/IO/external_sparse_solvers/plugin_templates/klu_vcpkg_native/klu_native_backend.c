#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "klu.h"

typedef struct {
    PyObject_HEAD
    klu_symbolic *symbolic;
} SymbolicHandleObject;

typedef struct {
    PyObject_HEAD
    klu_symbolic *symbolic;
    klu_numeric *numeric;
} NumericHandleObject;

static PyTypeObject SymbolicHandleType;
static PyTypeObject NumericHandleType;

static void free_symbolic_klu(klu_symbolic **symbolic_ptr) {
    klu_common common;
    if (symbolic_ptr == NULL || *symbolic_ptr == NULL) {
        return;
    }
    klu_defaults(&common);
    klu_free_symbolic(symbolic_ptr, &common);
}

static void free_numeric_klu(klu_numeric **numeric_ptr) {
    klu_common common;
    if (numeric_ptr == NULL || *numeric_ptr == NULL) {
        return;
    }
    klu_defaults(&common);
    klu_free_numeric(numeric_ptr, &common);
}

static void SymbolicHandle_dealloc(SymbolicHandleObject *self) {
    if (self->symbolic != NULL) {
        free_symbolic_klu(&self->symbolic);
    }
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static void NumericHandle_dealloc(NumericHandleObject *self) {
    if (self->numeric != NULL) {
        free_numeric_klu(&self->numeric);
    }
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int copy_numpy_int32_array(PyObject *obj, int32_t **out_data, Py_ssize_t *out_size) {
    PyObject *sequence = PySequence_Fast(obj, "Expected an integer sequence");
    Py_ssize_t size, index;
    int32_t *buffer;

    if (sequence == NULL) {
        return 0;
    }

    size = PySequence_Fast_GET_SIZE(sequence);
    buffer = (int32_t *) malloc(sizeof(int32_t) * (size_t) size);
    if (buffer == NULL) {
        Py_DECREF(sequence);
        PyErr_NoMemory();
        return 0;
    }

    for (index = 0; index < size; index++) {
        PyObject *item = PySequence_Fast_GET_ITEM(sequence, index);
        long value = PyLong_AsLong(item);
        if (PyErr_Occurred()) {
            free(buffer);
            Py_DECREF(sequence);
            return 0;
        }
        buffer[index] = (int32_t) value;
    }

    Py_DECREF(sequence);
    *out_data = buffer;
    *out_size = size;
    return 1;
}

static int copy_numpy_float64_array(PyObject *obj, double **out_data, Py_ssize_t *out_size) {
    PyObject *sequence = PySequence_Fast(obj, "Expected a float sequence");
    Py_ssize_t size, index;
    double *buffer;

    if (sequence == NULL) {
        return 0;
    }

    size = PySequence_Fast_GET_SIZE(sequence);
    buffer = (double *) malloc(sizeof(double) * (size_t) size);
    if (buffer == NULL) {
        Py_DECREF(sequence);
        PyErr_NoMemory();
        return 0;
    }

    for (index = 0; index < size; index++) {
        PyObject *item = PySequence_Fast_GET_ITEM(sequence, index);
        double value = PyFloat_AsDouble(item);
        if (PyErr_Occurred()) {
            free(buffer);
            Py_DECREF(sequence);
            return 0;
        }
        buffer[index] = value;
    }

    Py_DECREF(sequence);
    *out_data = buffer;
    *out_size = size;
    return 1;
}

static PyObject *create_symbolic_handle(klu_symbolic *symbolic) {
    SymbolicHandleObject *handle = (SymbolicHandleObject *) SymbolicHandleType.tp_alloc(&SymbolicHandleType, 0);
    if (handle == NULL) {
        return NULL;
    }
    handle->symbolic = symbolic;
    return (PyObject *) handle;
}

static PyObject *create_numeric_handle(klu_symbolic *symbolic, klu_numeric *numeric) {
    NumericHandleObject *handle = (NumericHandleObject *) NumericHandleType.tp_alloc(&NumericHandleType, 0);
    if (handle == NULL) {
        return NULL;
    }
    handle->symbolic = symbolic;
    handle->numeric = numeric;
    return (PyObject *) handle;
}

static PyObject *klu_native_analyze(PyObject *self, PyObject *args) {
    PyObject *indptr_obj;
    PyObject *indices_obj;
    int n;
    int32_t *ap = NULL;
    int32_t *ai = NULL;
    Py_ssize_t ap_size = 0;
    Py_ssize_t ai_size = 0;
    klu_common common;
    klu_symbolic *symbolic;
    PyObject *result;

    if (!PyArg_ParseTuple(args, "OOi", &indptr_obj, &indices_obj, &n)) {
        return NULL;
    }

    if (!copy_numpy_int32_array(indptr_obj, &ap, &ap_size)) {
        return NULL;
    }
    if (!copy_numpy_int32_array(indices_obj, &ai, &ai_size)) {
        free(ap);
        return NULL;
    }

    klu_defaults(&common);
    symbolic = klu_analyze((int32_t) n, ap, ai, &common);
    free(ap);
    free(ai);

    if (symbolic == NULL) {
        PyErr_Format(PyExc_RuntimeError, "KLU analyze failed with status %d", common.status);
        return NULL;
    }

    result = create_symbolic_handle(symbolic);
    if (result == NULL) {
        free_symbolic_klu(&symbolic);
    }
    return result;
}

static PyObject *klu_native_factorize(PyObject *self, PyObject *args) {
    PyObject *indptr_obj;
    PyObject *indices_obj;
    PyObject *data_obj;
    PyObject *symbolic_obj;
    int32_t *ap = NULL;
    int32_t *ai = NULL;
    double *ax = NULL;
    Py_ssize_t ap_size = 0;
    Py_ssize_t ai_size = 0;
    Py_ssize_t ax_size = 0;
    klu_common common;
    klu_numeric *numeric;
    SymbolicHandleObject *symbolic_handle;
    PyObject *result;

    if (!PyArg_ParseTuple(args, "OOOO", &indptr_obj, &indices_obj, &data_obj, &symbolic_obj)) {
        return NULL;
    }

    if (!PyObject_TypeCheck(symbolic_obj, &SymbolicHandleType)) {
        PyErr_SetString(PyExc_TypeError, "Expected a SymbolicHandle object");
        return NULL;
    }

    symbolic_handle = (SymbolicHandleObject *) symbolic_obj;

    if (!copy_numpy_int32_array(indptr_obj, &ap, &ap_size)) {
        return NULL;
    }
    if (!copy_numpy_int32_array(indices_obj, &ai, &ai_size)) {
        free(ap);
        return NULL;
    }
    if (!copy_numpy_float64_array(data_obj, &ax, &ax_size)) {
        free(ap);
        free(ai);
        return NULL;
    }

    klu_defaults(&common);
    numeric = klu_factor(ap, ai, ax, symbolic_handle->symbolic, &common);
    free(ap);
    free(ai);
    free(ax);

    if (numeric == NULL) {
        PyErr_Format(PyExc_RuntimeError, "KLU factorization failed with status %d", common.status);
        return NULL;
    }

    result = create_numeric_handle(symbolic_handle->symbolic, numeric);
    if (result == NULL) {
        free_numeric_klu(&numeric);
    }
    return result;
}

static PyObject *klu_native_solve(PyObject *self, PyObject *args) {
    PyObject *rhs_obj;
    PyObject *numeric_obj;
    NumericHandleObject *numeric_handle;
    double *rhs_data = NULL;
    Py_ssize_t rhs_size = 0;
    klu_common common;
    PyObject *result = NULL;
    PyObject *list_obj = NULL;
    Py_ssize_t index;
    int success;

    if (!PyArg_ParseTuple(args, "OO", &numeric_obj, &rhs_obj)) {
        return NULL;
    }

    if (!PyObject_TypeCheck(numeric_obj, &NumericHandleType)) {
        PyErr_SetString(PyExc_TypeError, "Expected a NumericHandle object");
        return NULL;
    }

    numeric_handle = (NumericHandleObject *) numeric_obj;

    if (!copy_numpy_float64_array(rhs_obj, &rhs_data, &rhs_size)) {
        return NULL;
    }

    klu_defaults(&common);
    success = klu_solve(
        numeric_handle->symbolic,
        numeric_handle->numeric,
        (int32_t) rhs_size,
        1,
        rhs_data,
        &common
    );

    if (success == 0) {
        free(rhs_data);
        PyErr_Format(PyExc_RuntimeError, "KLU solve failed with status %d", common.status);
        return NULL;
    }

    list_obj = PyList_New(rhs_size);
    if (list_obj == NULL) {
        free(rhs_data);
        return NULL;
    }

    for (index = 0; index < rhs_size; index++) {
        PyObject *value_obj = PyFloat_FromDouble(rhs_data[index]);
        if (value_obj == NULL) {
            free(rhs_data);
            Py_DECREF(list_obj);
            return NULL;
        }
        PyList_SET_ITEM(list_obj, index, value_obj);
    }

    free(rhs_data);
    result = list_obj;
    return result;
}

static PyMethodDef module_methods[] = {
    {"analyze", klu_native_analyze, METH_VARARGS, "Analyze a CSC pattern with KLU."},
    {"factorize", klu_native_factorize, METH_VARARGS, "Factorize a CSC matrix with KLU."},
    {"solve", klu_native_solve, METH_VARARGS, "Solve a system using a KLU factorization."},
    {NULL, NULL, 0, NULL}
};

static PyTypeObject SymbolicHandleType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "klu_native_backend.SymbolicHandle",
    .tp_basicsize = sizeof(SymbolicHandleObject),
    .tp_dealloc = (destructor) SymbolicHandle_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
};

static PyTypeObject NumericHandleType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "klu_native_backend.NumericHandle",
    .tp_basicsize = sizeof(NumericHandleObject),
    .tp_dealloc = (destructor) NumericHandle_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
};

static struct PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "klu_native_backend",
    "Native KLU backend for VeraGrid EMT.",
    -1,
    module_methods,
};

PyMODINIT_FUNC PyInit_klu_native_backend(void) {
    PyObject *module;

    if (PyType_Ready(&SymbolicHandleType) < 0) {
        return NULL;
    }
    if (PyType_Ready(&NumericHandleType) < 0) {
        return NULL;
    }

    module = PyModule_Create(&module_definition);
    if (module == NULL) {
        return NULL;
    }

    Py_INCREF(&SymbolicHandleType);
    PyModule_AddObject(module, "SymbolicHandle", (PyObject *) &SymbolicHandleType);
    Py_INCREF(&NumericHandleType);
    PyModule_AddObject(module, "NumericHandle", (PyObject *) &NumericHandleType);
    return module;
}
