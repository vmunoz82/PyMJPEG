/*

  Copyright (C) 2012 Victor Munoz <vmunoz@ingenieria-inversa.cl>

  for demonstration purpose only, not for redistribution.

*/

#include "c_jpegdev.h"
#define _USE_MATH_DEFINES
#include <math.h>

double naive_idct_table[8][8];

void naive_idct_gen_table() {
    int32_t u, x;
    
    for(u=0; u<8; u++) {
        for(x=0; x<8; x++) {
            naive_idct_table[u][x]=(x==0?sqrt(2)*0.25:0.5) * cos(M_PI * x * (2 * u + 1) / 16);
        }
    }
}

void naive_idct_1d(double *msrc, double *mout, int32_t a, int32_t b) {
    int32_t u, w;
    double t;
    
    for(u=0; u<8; ++u) {
        t=0;
        for(w=0; w<8; ++w) t+=msrc[w<<a|b]*naive_idct_table[u][w];
        mout[u<<a|b]=t;
    }
}

void naive_idct_2d(int32_t *src) {
    int32_t i;
    double m0[64];
    double m1[64];
    
    for(i=0; i<64; ++i)
        m0[i]=src[i];

    for(i=0; i<8; ++i)
        naive_idct_1d(m0, m1, 3, i);
    for(i=0; i<8; ++i)
        naive_idct_1d(m1, m0, 0, i<<3);
        
    for(i=0; i<64; ++i)
        src[i]=(int32_t)m0[i];
}

/* Chen-Wang algorithm. */
#define W1 2841
#define W2 2676
#define W3 2408
#define W5 1609
#define W6 1108
#define W7 565

void idct_1da(int32_t *src) {
    int32_t x0, x1, x2, x3, x4, x5, x6, x7, x8;
    
    x1=src[4]<<11;
    x2=src[6];
    x3=src[2];
    x4=src[1];
    x5=src[7];
    x6=src[5];
    x7=src[3];
    
    if ((x1|x2|x3|x4|x5|x6|x7)==0) {
        src[4]=src[5]=src[6]=src[7]=src[0]<<3;
        src[0]=src[1]=src[2]=src[3]=src[0]<<3;
        return;
    }
    
    x0=(src[0]<<11)+128;
    
    x8=W7*(x4+x5);
    x4=x8+(W1-W7)*x4;
    x5=x8-(W1+W7)*x5;
    x8=W3*(x6+x7);
    x6=x8-(W3-W5)*x6;
    x7=x8-(W3+W5)*x7;
    
    x8=x0+x1;
    x0-=x1;
    x1=W6*(x3+x2);
    x2=x1-(W2+W6)*x2;
    x3=x1+(W2-W6)*x3;
    x1=x4+x6;
    x4-=x6;
    x6=x5+x7;
    x5-=x7;
    
    x7=x8+x3;
    x8-=x3;
    x3=x0+x2;
    x0-=x2;
    x2=(181*(x4+x5)+128)>>8;
    x4=(181*(x4-x5)+128)>>8;

    src[0]=(x7+x1)>>8;
    src[1]=(x3+x2)>>8;
    src[2]=(x0+x4)>>8;
    src[3]=(x8+x6)>>8;
    src[4]=(x8-x6)>>8;
    src[5]=(x0-x4)>>8;
    src[6]=(x3-x2)>>8;
    src[7]=(x7-x1)>>8;
}

int32_t clip(int32_t v) {
    return (v<-128?-128:(v>127?127:v));
}

void idct_1db(int32_t *src) {
    int32_t x0, x1, x2, x3, x4, x5, x6, x7, x8;
    
    x1=src[32]<<8;
    x2=src[48];
    x3=src[16];
    x4=src[8];
    x5=src[56];
    x6=src[40];
    x7=src[24];
    
    if ((x1|x2|x3|x4|x5|x6|x7)==0) {
        src[32]=src[40]=src[48]=src[56]=src[0]= src[8]= src[16]=src[24]=clip((src[0]+32)>>6);
        return;
    }
    
    x0=(src[0]<<8)+8192;
    
    x8=W7*(x4+x5)+4;
    x4=(x8+(W1-W7)*x4)>>3;
    x5=(x8-(W1+W7)*x5)>>3;
    x8=W3*(x6+x7)+4;
    x6=(x8-(W3-W5)*x6)>>3;
    x7=(x8-(W3+W5)*x7)>>3;
    
    x8=x0+x1;
    x0-=x1;
    x1=W6*(x3+x2)+4;
    x2=(x1-(W2+W6)*x2)>>3;
    x3=(x1+(W2-W6)*x3)>>3;
    x1=x4+x6;
    x4-=x6;
    x6=x5+x7;
    x5-=x7;
    
    x7=x8+x3;
    x8-=x3;
    x3=x0+x2;
    x0-=x2;
    x2=(181*(x4+x5)+128)>>8;
    x4=(181*(x4-x5)+128)>>8;
 
    src[0]= clip((x7+x1)>>14);
    src[8]= clip((x3+x2)>>14);
    src[16]=clip((x0+x4)>>14);
    src[24]=clip((x8+x6)>>14);
    src[32]=clip((x8-x6)>>14);
    src[40]=clip((x0-x4)>>14);
    src[48]=clip((x3-x2)>>14);
    src[56]=clip((x7-x1)>>14);
}

void idct_2d(int32_t *src) {
    int32_t i;
    for (i=0; i<8; ++i)
        idct_1da(&src[i<<3]);
    for (i=0; i<8; ++i)
        idct_1db(&src[i]);
}

void ycbcr2rgb(long *in, long *out) {
    static double reciprocal_const1=1/0.587;
    
    double y,cb,cr;
    double r,g,b;
    
    y=in[0];
    cb=in[1];
    cr=in[2];

    r=cr*(2-2*0.299)+y;
    b=cb*(2-2* 0.114)+y;
    g=(y-b*0.114-r*0.299)*reciprocal_const1;
    
    r+=128;
    g+=128;
    b+=128;
    r=r<0?0:r;
    r=r>255?255:r;
    g=g<0?0:g;
    g=g>255?255:g;
    b=b<0?0:b;
    b=b>255?255:b;

    out[0]=(long)r;
    out[1]=(long)g;
    out[2]=(long)b;
}
