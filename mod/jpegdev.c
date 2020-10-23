/*

  Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>

  for demonstration purpose only, not for redistribution.

*/

#include <Python.h>
#include "c_jpegdev.h"

static char jpegdev_doc[] =
"This module implement some basic JPEG functionality like IDCT and YCbCr to RGB transformations.";

static PyObject*
jpegdev_idct_2d(PyObject *self, PyObject *args)
{
    PyObject *l, *b;
    int i;
    int t[64];

    l=args;

    if(!PyList_Check(l)) return NULL;

    if(PyList_Size(l)!=64) return NULL;

    for(i=0; i<64; i++) {
        b = PyList_GetItem(l, i);
        if(!PyInt_Check(b)) {
            printf("elemento %d no es entero\n", i);
            return NULL;
        }
        t[i]=PyInt_AsLong(b);
    }

    idct_2d(t);
    Py_INCREF(l);
    for(i=0; i<64; i++) {
        PyList_SetItem(l, i, PyInt_FromLong(t[i]));
    }

    return l;
}

static PyObject*
jpegdev_naive_idct_2d(PyObject *self, PyObject *args)
{
    PyObject *l, *b;
    int i;
    int t[64];

    l=args;

    if(!PyList_Check(l)) return NULL;

    if(PyList_Size(l)!=64) return NULL;

    for(i=0; i<64; i++) {
        b = PyList_GetItem(l, i);
        if(!PyInt_Check(b)) {
            printf("elemento %d no es entero\n", i);
            return NULL;
        }
        t[i]=PyInt_AsLong(b);
    }

    naive_idct_2d(t);
    Py_INCREF(l);
    for(i=0; i<64; i++) {
        PyList_SetItem(l, i, PyInt_FromLong(t[i]));
    }

    return l;
}
static char idct_2d_doc[] =
"idct_2d(matrix)\n"
"\n"
"Apply a 2d transformation to a 8x8 matrix.";

static char naive_idct_2d_doc[] =
"naive_idct_2d(matrix)\n"
"\n"
"Apply a 2d transformation to a 8x8 matrix.";

static char ycbcr2rgb_doc[] =
"ycbcr2rgb(y, cb, cr)\n"
"\n"
"Apply YCbCr to RGB transformation.\n"
"Returns a (r, g, b) tuple.";


static PyObject*
jpegdev_ycbcr2rgb(PyObject *self, PyObject *args) {
    PyObject *y, *cb, *cr;
    long ycbcr[3];
    long rgb[3];
    PyObject* tuple;

    if(!PyArg_UnpackTuple(args, "ycbcr2rgb", 3, 3, &y, &cb, &cr)) {
        return NULL;
    }

    if(!(PyInt_Check(y) && PyInt_Check(cb) && PyInt_Check(cr))) {
        printf("parametros deben ser enteros\n");
        return NULL;
    }

    ycbcr[0]=PyInt_AsLong(y);
    ycbcr[1]=PyInt_AsLong(cb);
    ycbcr[2]=PyInt_AsLong(cr);

    ycbcr2rgb(ycbcr, rgb);

    tuple = PyList_New(3);
    PyList_SetItem(tuple, 0, PyInt_FromLong(rgb[0]));
    PyList_SetItem(tuple, 1, PyInt_FromLong(rgb[1]));
    PyList_SetItem(tuple, 2, PyInt_FromLong(rgb[2]));

    return tuple;
}


static PyMethodDef jpegdev_methods[] = {
    {"idct_2d",                  jpegdev_idct_2d,              METH_O,       idct_2d_doc},
    {"naive_idct_2d",      jpegdev_naive_idct_2d,              METH_O,       naive_idct_2d_doc},
    {"ycbcr2rgb",              jpegdev_ycbcr2rgb,              METH_VARARGS, ycbcr2rgb_doc},
    {NULL, NULL}
};

PyMODINIT_FUNC
initjpegdev(void)
{
    naive_idct_gen_table();
    Py_InitModule3("jpegdev", jpegdev_methods, jpegdev_doc);
}
