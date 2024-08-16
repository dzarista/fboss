MKDIR ?= mkdir
CP ?= cp
CXX := g++
CXXFLAGS := -std=c++1z -Wall -Wextra
LIBS := -lstdc++fs

PROG := psu-upgrade
OBJS := PsuUpdate.o

all: $(PROG)

$(PROG): main.cpp $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LIBS)

PsuUpdate.o: PsuUpdate.cpp PsuUpdate.h smbus.h

.PHONY: clean

install:
	$(MKDIR) -p $(DESTDIR)
	$(CP) $(PROG) $(DESTDIR)

clean:
	$(RM) -rf $(OBJS) $(PROG)
