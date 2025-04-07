CC = gcc
CFLAGS = -g -Wall

SOURCES = strip_arista_header.c
OBJECTS = $(SOURCES:.c=.o)
TARGET = strip_arista_header

$(TARGET) : $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^

clean:
	@rm -f $(TARGET) $(OBJECTS)
