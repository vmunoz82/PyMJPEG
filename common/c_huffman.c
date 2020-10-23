/*

  Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>

  for demonstration purpose only, not for redistribution.

*/

#include "c_huffman.h"

void huff_stream_init(t_huff_stream_ctx *s, uint8_t *stream, uint32_t idx) {
    s->hdata=stream;
    s->idx=idx;
}

void huff_sync(t_huff_stream_ctx *s) {
    s->idx = ((s->idx + 7) >> 3) << 3;
}

#ifdef HUFF_BIG_TABLE

void huff_table_init(t_huff_table_ctx *t, uint8_t *sizes, uint8_t *symbols) {
    int32_t i,j,k,l,s;
    uint32_t code;
    uint32_t ncode;
    
    code=0;
    
    l=0;
    for(i=0,s=15; i<16; i++, s--) {        
        for(j=0; j<sizes[i]; j++) {
            ncode=code<<s;
            
            for(k=0; k<(1<<s); ++k) {
                t->symbols2[ncode|k]=symbols[l];
            }
            t->bits[symbols[l]]=i+1;
            l++;
            code++;
        }
        code<<=1;
    }
}

uint32_t huff_get_symbol(t_huff_stream_ctx *s, t_huff_table_ctx *t) { 
    int32_t i;
    uint32_t u;
    uint32_t symbol;
    
    i=s->idx>>3;
    u=s->hdata[i]<<16|s->hdata[i+1]<<8|s->hdata[i+2];
    u>>=(8-(s->idx&7));
    u&=0xFFFF;

    symbol=t->symbols2[u];
    s->idx+=t->bits[symbol];
    return symbol;
}

#else

void huff_table_init(t_huff_table_ctx *h, uint8_t *sizes, uint8_t *symbols) {
    int32_t i,j,cc;
    uint32_t code;
    
    code=0;
    cc=0;
    
    for(i=0; i<16; i++) {
        cc+=sizes[i];
        h->csizes[i]=cc-1;
        for(j=0; j<sizes[i]; j++) code++;
        h->last[i]=code-1;
        code<<=1;
    }
    
    memcpy(h->symbols, symbols, cc);
}

uint32_t huff_get_symbol(t_huff_stream_ctx *h, t_huff_table_ctx *t) { 
    int32_t i;
    int32_t v;
    
    v=0;

    for(i=0; i<16; i++) {
        v=(v<<1) | ((h->hdata[h->idx>>3]>>((~h->idx)&7))&1);
        h->idx++;
        
        if(v<=t->last[i]) {
            return t->symbols[t->csizes[i]-(t->last[i]-v)];
        }
    }
    return 0;
}

#endif

uint32_t mask16[17]={
0x0000, 
0x0001, 0x0003, 0x0007, 0x000F, 
0x001F, 0x003F, 0x007F, 0x00FF, 
0x01FF, 0x03FF, 0x07FF, 0x0FFF, 
0x1FFF, 0x3FFF, 0x7FFF, 0xFFFF
};

int32_t huff_get_jpeg_value(t_huff_stream_ctx *s, int32_t bits) {
    uint32_t u;
    uint32_t m=mask16[bits];
        
    int32_t i;
    i=s->idx>>3;
    u=s->hdata[i]<<16|s->hdata[i+1]<<8|s->hdata[i+2];    
    
    u>>=24-bits-(s->idx&7);
    u&=m;
    
    s->idx+=bits;
    
    if(u&(1<<(bits-1))) return u;
    return u - m;
}
