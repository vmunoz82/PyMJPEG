#ifdef _MSC_VER
typedef __int8 int8_t;
typedef unsigned __int8 uint8_t;
typedef __int32 int32_t;
typedef unsigned __int32 uint32_t;
#else
#include <stdint.h>
#endif

#define HUFF_BIG_TABLE

#ifdef HUFF_BIG_TABLE
typedef struct t_huff_table_ctx {
    uint8_t symbols2[0x10000];
    uint8_t bits[256];
} t_huff_table_ctx;

#else
typedef struct t_huff_table_ctx {
    int32_t csizes[16];
    int32_t last[16];
    uint8_t symbols[256];
} t_huff_table_ctx;
#endif

typedef struct t_huff_stream_ctx {
    int32_t idx;
    uint8_t *hdata;
} t_huff_stream_ctx;

void huff_stream_init(t_huff_stream_ctx *s, uint8_t *stream, uint32_t idx);

void huff_table_init(t_huff_table_ctx *t, uint8_t *sizes, uint8_t *symbols);

void huff_sync(t_huff_stream_ctx *s);

uint32_t huff_get_symbol(t_huff_stream_ctx *s, t_huff_table_ctx *t);

int32_t huff_get_jpeg_value(t_huff_stream_ctx *s, int32_t bits);
