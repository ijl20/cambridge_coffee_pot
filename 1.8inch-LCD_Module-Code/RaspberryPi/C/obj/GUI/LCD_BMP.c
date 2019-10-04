#include "LCD_BMP.h"
#include "LCD_1in8.h"
#include "LCD_GUI.h"
#include <stdio.h>	//fseek fread
#include <fcntl.h>
#include <unistd.h>
#include <stdint.h>
#include <stdlib.h>	//memset
extern LCD_DIS sLCD_DIS;

uint8_t LCD_ShowBmp(const char *path)
{
    FILE *fp;                     //Define a file pointer 
    BMPFILEHEADER bmpFileHeader;  //Define a bmp file header structure
    BMPINF bmpInfoHeader;         //Define a bmp bitmap header structure 

    //Binary file open
    if((fp = fopen(path, "rb")) == NULL) { // fp = 0x00426aa0
        printf("Cann't open the file!\n");
        return 0;
    }

    //Set the file pointer from the beginning
    fseek(fp, 0, SEEK_SET);                            // fp = 0x00426aa0
    fread(&bmpFileHeader, sizeof(BMPFILEHEADER), 1, fp);//	sizeof(BMPFILEHEADER) must be 14,
	fread(&bmpInfoHeader, sizeof(BMPINF), 1, fp);
    //printf("sizeof(BMPFILEHEADER) = %d\n", sizeof(BMPFILEHEADER));
    //printf("sizeof(bmpInfoHeader) = %d\n", sizeof(bmpInfoHeader));

    //file header information
	// printf("********************************************************\r\n" );
    // printf("file header information:\n"                                   );
    // printf(" FileSize         : %ld  \r\n" , bmpFileHeader.bSize          );
    // printf(" Reserv1          : %d  \r\n"  , bmpFileHeader.bReserved1     );
    // printf(" Reserv2          : %d  \r\n"  , bmpFileHeader.bReserved2     );
    // printf(" FileOffset       : %ld  \r\n" , bmpFileHeader.bOffset        );
	
    //bitmap header information
	// printf("********************************************************\r\n" );
    // printf("bitmap header information:\n"                                 );
	// printf(" DIBHeaderSize    : %ld  \r\n" , bmpInfoHeader.bInfoSize      );
    // printf(" ImageWidth       : %ld  \r\n" , bmpInfoHeader.bWidth         );
    // printf(" ImageHight       : %ld  \r\n" , bmpInfoHeader.bHeight        );
    // printf(" Planes           : %d  \r\n"  , bmpInfoHeader.bPlanes        );
    // printf(" BPP              : %d  \r\n"  , bmpInfoHeader.bBitCount      );
    // printf(" Compression      : %ld  \r\n" , bmpInfoHeader.bCompression   );
    // printf(" ImageSize        : %ld  \r\n" , bmpInfoHeader.bmpImageSize   );
    // printf(" XPPM             : %ld  \r\n" , bmpInfoHeader.bXPelsPerMeter );
    // printf(" YPPM             : %ld  \r\n" , bmpInfoHeader.bYPelsPerMeter );
    // printf(" CCT              : %ld  \r\n" , bmpInfoHeader.bClrUsed       );
    // printf(" ICC              : %ld  \r\n" , bmpInfoHeader.bClrImportant  );
    
	int row, col;
    short data;
	RGBQUAD rgb;
	int len = bmpInfoHeader.bBitCount / 8;    //RGB888,one 3 byte = 1 bitbmp
	
	//get bmp data and show
    // LCD_SetGramScanWay(1);
	fseek(fp, bmpFileHeader.bOffset, SEEK_SET);
    for(row = 0; row < bmpInfoHeader.bHeight; row++) {
        for(col = 0; col < bmpInfoHeader.bWidth; col++) {
			if(fread((char *)&rgb, 1, len, fp) != len){
				perror("get bmpdata:\r\n");
				break;
			}		
            data = RGB((rgb.rgbRed), (rgb.rgbGreen), (rgb.rgbBlue));
            Paint_SetPixel(col, \
                               bmpInfoHeader.bHeight - 1 -row, data);
            // Paint_SetPixel(col,row,data);
        }
    }
	fclose(fp);
	LCD_SetGramScanWay(SCAN_DIR_DFT);
    return 0;
}