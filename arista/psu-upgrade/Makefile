MKDIR ?= mkdir
CP ?= cp
CXX := g++
CXXFLAGS := -std=c++1z -Wall -Wextra
LIBS := -lstdc++fs

PROG := psu-upgrade
OBJS := PsuUpdate.o PsuModels.o DeviceHandler.o

all: $(PROG)

$(PROG): main.cpp $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LIBS)

PsuUpdate.o: PsuUpdate.cpp PsuUpdate.h smbus.h PsuModels.h DeviceHandler.h

PsuModels.o: PsuModels.h PsuModels.cpp DeviceHandler.h

DeviceHandler.o: DeviceHandler.h DeviceHandler.cpp

.PHONY: clean

install:
	$(MKDIR) -p $(DESTDIR)
	$(CP) $(PROG) $(DESTDIR)

clean:
	$(RM) -rf $(OBJS) $(PROG)
