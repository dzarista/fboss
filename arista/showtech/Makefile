MKDIR ?= mkdir
CP ?= cp
CXX := g++
CXXFLAGS := -std=c++1z -Wall -Wextra
LIBS := -lstdc++fs

PROG := platform-showtech
OBJS := DarwinShowtech.o MeruShowtech.o Showtech.o ShowtechUtils.o PsuShowtech.o CfmShowtech.o

all: $(PROG)

$(PROG): main.cpp $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LIBS)

DarwinShowtech.o: DarwinShowtech.cpp DarwinShowtech.h Showtech.h

MeruShowtech.o: MeruShowtech.cpp MeruShowtech.h Showtech.h

ShowtechUtils.o: ShowtechUtils.cpp ShowtechUtils.h

Showtech.o: Showtech.cpp Showtech.h ShowtechUtils.h

PsuShowtech.o: PsuShowtech.cpp PsuShowtech.h

CfmShowtech.o: CfmShowtech.cpp CfmShowtech.h

.PHONY: clean

install:
	$(MKDIR) -p $(DESTDIR)
	$(CP) $(PROG) $(DESTDIR)

clean:
	$(RM) -rf $(OBJS) $(PROG)
