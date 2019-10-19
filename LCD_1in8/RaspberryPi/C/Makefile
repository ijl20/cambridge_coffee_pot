DIR_FONTS = ./Fonts
DIR_CONFIG = ./obj/Config
DIR_Drive = ./obj/LCD
DIR_GUI = ./obj/GUI
DIR_OBJ = ./obj
DIR_BIN = ./bin

OBJ_C = $(wildcard ${DIR_FONTS}/*.c ${DIR_OBJ}/*.c ${DIR_CONFIG}/*.c ${DIR_Drive}/*.c ${DIR_GUI}/*.c)
OBJ_O = $(patsubst %.c,${DIR_BIN}/%.o,$(notdir ${OBJ_C}))

TARGET = main
#BIN_TARGET = ${DIR_BIN}/${TARGET}

CC = gcc

DEBUG = -g -O0 -Wall
CFLAGS += $(DEBUG)

# USELIB = USE_BCM2835_LIB
# USELIB = USE_WIRINGPI_LIB
USELIB = USE_DEV_LIB
DEBUG = -D $(USELIB)
ifeq ($(USELIB), USE_BCM2835_LIB)
    LIB = -lbcm2835 -lm 
else ifeq ($(USELIB), USE_WIRINGPI_LIB)
    LIB = -lwiringPi -lm 
else
    LIB = -lm
endif


${TARGET}:${OBJ_O}
	$(CC) $(CFLAGS) $(OBJ_O) -o $@ $(LIB)  -I $(DIR_CONFIG) -I $(DIR_GUI) -I $(DIR_Drive) -I $(DIR_FONTS) -I $(DIR_OBJ)

${DIR_BIN}/%.o : $(DIR_OBJ)/%.c 
	$(CC) $(CFLAGS) -c  $< -o $@ $(LIB) -I $(DIR_CONFIG) -I $(DIR_GUI) -I $(DIR_Drive) -I $(DIR_FONTS)

${DIR_BIN}/%.o:$(DIR_GUI)/%.c
	$(CC) $(CFLAGS) -c  $< -o $@ -I $(DIR_CONFIG) -I $(DIR_Drive) -I $(DIR_FONTS) -I $(DIR_GUI)

${DIR_BIN}/%.o:$(DIR_Drive)/%.c
	$(CC) $(CFLAGS) -c  $< -o $@ -I $(DIR_CONFIG) -I $(DIR_GUI) -I $(DIR_FONTS) -I $(DIR_Drive)

${DIR_BIN}/%.o:$(DIR_FONTS)/%.c
	$(CC) $(CFLAGS) -c  $< -o $@ 
 
${DIR_BIN}/%.o:$(DIR_CONFIG)/%.c
	$(CC) $(CFLAGS) -c  $< -o $@   

	
clean :
	rm $(DIR_BIN)/*.* 
	rm $(TARGET)