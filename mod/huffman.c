/*

  Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>

  for demonstration purpose only, not for redistribution.

*/

#include <Python.h>
#include "structmember.h"
#include "c_huffman.h"

/*******************/
typedef struct {
    PyObject_HEAD

    t_huff_table_ctx *htables[256];
    int htables_count;
    t_huff_stream_ctx hstream;
    PyObject *py_stream;
} Huf;

static PyObject *
Huf_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    Huf *self;

    //printf("Huf_new\n");

    self = (Huf *)type->tp_alloc(type, 0);

    if (self!=NULL) {
        memset(&self->htables, 0, sizeof(self->htables));
        self->htables_count=0;
        memset(&self->hstream, 0, sizeof(self->hstream));
        self->py_stream=NULL;
    }

    return (PyObject *)self;
}

static int
Huf_init(Huf *self, PyObject *args, PyObject *kwds)
{
    //printf("Huf_init\n");

    return 0;
}

static void
Huf_dealloc(Huf *self)
{
    int i;

    //printf("Huf_dealloc\n");

    if(self->py_stream) {
        Py_DECREF(self->py_stream);
        for(i=0; i<self->htables_count; i++) {
            free(self->htables[i]);
        }
    }
    self->ob_type->tp_free((PyObject*)self);
}

static PyMemberDef Huf_members[] = {
    {NULL}  /* Sentinel */
};

/*******************/

static PyObject *Huf_stream_init(Huf *self, PyObject *args) {
    PyObject *stream, *idx;
    char *_stream;

    if(!PyArg_UnpackTuple(args, "huff_stream_init", 2, 2, &stream, &idx)) {
        return NULL;
    }

    if(PyByteArray_Check(stream)) {
        if(PyInt_Check(idx)) {
            _stream=PyByteArray_AsString(stream);
            self->py_stream=stream;
            Py_INCREF(self->py_stream);

            huff_stream_init(&self->hstream, (unsigned char *)_stream, PyInt_AsLong(idx));
        } else fprintf(stderr, "Huf_stream_init: error 2.\n");
    } else fprintf(stderr, "Huf_stream_init: error 1.\n");

    Py_RETURN_NONE;
}

static PyObject *Huf_table_init(Huf *self, PyObject *args) {
    PyObject *sizes, *symbols, *ret;

    char *_sizes, *_symbols;
    Py_ssize_t sz0,sz1;

    if(!PyArg_UnpackTuple(args, "huff_table_init", 2, 2, &sizes, &symbols)) {
        return NULL;
    }

    if(self->htables_count>=255) {
        fprintf(stderr, "Huf_table_init: error 1.\n");
        return NULL;
    }

    self->htables[self->htables_count]=(t_huff_table_ctx *)malloc(sizeof(t_huff_table_ctx));
    memset(self->htables[self->htables_count], 0, sizeof(t_huff_table_ctx));
    self->htables_count++;

    ret=PyInt_FromLong(-1);

    if(PyString_Check(sizes)) {
        if(PyString_Check(symbols)) {
            PyString_AsStringAndSize(sizes, &_sizes, &sz0);
            PyString_AsStringAndSize(symbols, &_symbols, &sz1);

            huff_table_init(self->htables[self->htables_count-1], (unsigned char *)_symbols, (unsigned char *)_sizes);

            ret=PyInt_FromLong(self->htables_count-1);
        } else fprintf(stderr, "Huf_table_init: error 3.\n");
    } else fprintf(stderr, "Huf_table_init: error 2.\n");

    Py_INCREF(ret);
    return ret;
}

static PyObject *Huf_sync(Huf *self) {
    huff_sync(&self->hstream);

    Py_RETURN_NONE;
}

static PyObject *Huf_get_symbol(Huf *self, PyObject *args) {
    PyObject *table_idx, *ret;
    long _table_idx;
    long _ret;

    table_idx=args;
    ret=PyInt_FromLong(-1);
    if(PyInt_Check(table_idx)) {
        _table_idx=PyInt_AsLong(table_idx);
        _ret=huff_get_symbol(&self->hstream, self->htables[_table_idx]);
        ret=PyInt_FromLong(_ret);
    }

    Py_INCREF(ret);
    return ret;
}

static PyObject *Huf_get_jpeg_value(Huf *self, PyObject *args) {
    PyObject *bits, *ret;
    long _bits;
    long _ret;

    bits=args;

    ret=PyInt_FromLong(0);
    if(PyInt_Check(bits)) {
        _bits=PyInt_AsLong(bits);
        _ret=huff_get_jpeg_value(&self->hstream, _bits);
        ret=PyInt_FromLong(_ret);
    }

    Py_INCREF(ret);
    return ret;
}

static PyMethodDef Huf_methods[] = {
    {"stream_init",    (PyCFunction)Huf_stream_init,    METH_VARARGS,
     "Initialize a Huffman stream (buffer must have 2 additional bytes in size)."},
    {"table_init",     (PyCFunction)Huf_table_init,     METH_VARARGS,
     "Initialize a Huffman table. Returns the index inside the table array."},
    {"sync",           (PyCFunction)Huf_sync,           METH_NOARGS,
     "Synchronize a Huffman stream to an 8 bits boundary."},
    {"get_symbol",     (PyCFunction)Huf_get_symbol,     METH_O,
     "Retrieve the symbol at the current stream postion."},
    {"get_jpeg_value", (PyCFunction)Huf_get_jpeg_value, METH_O,
     "Retrieve the variable length integer (as per JPEG spec) at the current stream position."},
    {NULL}  /* Sentinel */
};

static PyTypeObject HufType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "huffman.Huffman",         /*tp_name*/
    sizeof(Huf),               /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)Huf_dealloc,   /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Huffman objects",         /* tp_doc */
    0,                           /* tp_traverse */
    0,                           /* tp_clear */
    0,                           /* tp_richcompare */
    0,                           /* tp_weaklistoffset */
    0,                           /* tp_iter */
    0,                           /* tp_iternext */
    Huf_methods,               /* tp_methods */
    Huf_members,               /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Huf_init,        /* tp_init */
    0,                         /* tp_alloc */
    Huf_new,                   /* tp_new */
};

static PyMethodDef module_methods[] = {
    {NULL}  /* Sentinel */
};

#ifndef PyMODINIT_FUNC    /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
inithuffman(void)
{
    PyObject* m;

    if (PyType_Ready(&HufType) < 0)
        return;

    m = Py_InitModule3("huffman", module_methods,
                       "Huffman decode module intend for JPEG decoding.");

    if (m == NULL)
      return;

    Py_INCREF(&HufType);
    PyModule_AddObject(m, "Huffman", (PyObject *)&HufType);
}
