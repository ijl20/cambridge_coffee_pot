#ifndef __LCD_BMP_H
#define __LCD_BMP_H

#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>

#define  RGB(r,g,b)         (((r>>3)<<11)|((g>>2)<<5)|(b>>3))

typedef unsigned char BYTE;//2 byte
typedef unsigned short WORD;//2 byte
typedef unsigned long DWORD;//4 byte
/****************************** Bitmap standard information*************************************/
/*Bitmap file header   14bit*/
typedef struct BMP_FILE_HEADER {
    WORD bType;                 //File identifier
    DWORD bSize;                //The size of the file
    WORD bReserved1;            //Reserved value, must be set to 0
    WORD bReserved2;            //Reserved value, must be set to 0
    DWORD bOffset;              //The offset from the beginning of the file header to the beginning of the image data bit
} __attribute__ ((packed)) BMPFILEHEADER;    // 14bit

/*Bitmap information header  40bit*/
typedef struct BMP_INFO {
    DWORD bInfoSize;            //The size of the header
    DWORD bWidth;               //The width of the image
    DWORD bHeight;              //The height of the image
    WORD bPlanes;               //The number of planes in the image
    WORD bBitCount;             //The number of bits per pixel
    DWORD bCompression;         //Compression type
    DWORD bmpImageSize;         //The size of the image, in bytes
    DWORD bXPelsPerMeter;       //Horizontal resolution
    DWORD bYPelsPerMeter;       //Vertical resolution
    DWORD bClrUsed;             //The number of colors used
    DWORD bClrImportant;        //The number of important colors
} __attribute__ ((packed)) BMPINF;

/*Color table: palette */
typedef struct RGB_QUAD {
    BYTE rgbBlue;               //Blue intensity
    BYTE rgbGreen;              //Green strength
    BYTE rgbRed;                //Red intensity
    BYTE rgbReversed;           //Reserved value
} __attribute__ ((packed)) RGBQUAD;
/**************************************** end ***********************************************/

uint8_t LCD_ShowBmp(const char *path);
#endif