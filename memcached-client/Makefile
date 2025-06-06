# Makefile for mcclient
ROOT_PATH?=../caladan/
include $(ROOT_PATH)/build/shared.mk

BW_LIBS = $(ROOT_PATH)/breakwater/libbw.a

mcclient_src = mcclient.cc
mcclient_obj = $(mcclient_src:.cc=.o)

librt_libs = $(ROOT_PATH)/bindings/cc/librt++.a
libbw_libs = $(ROOT_PATH)/breakwater/bindings/cc/libbw++.a
INC += -I$(ROOT_PATH)/breakwater/inc
INC += -I$(ROOT_PATH)/bindings
INC += -I$(ROOT_PATH)/breakwater/bindings/cc/inc

RUNTIME_LIBS := $(RUNTIME_LIBS) $(BW_LIBS) -lnuma

# must be first
all: mcclient

mcclient: $(mcclient_obj) $(librt_libs) $(libbw_libs) $(RUNTIME_DEPS)
	$(LDXX) -o $@ $(LDFLAGS) $(mcclient_obj) $(librt_libs) \
	$(libbw_libs) $(RUNTIME_LIBS)

# general build rules for all targets
src = $(mcclient_src)
obj = $(src:.cc=.o)
dep = $(obj:.o=.d)

ifneq ($(MAKECMDGOALS),clean)
-include $(dep)   # include all dep files in the makefile
endif

# rule to generate a dep file by using the C preprocessor
# (see man cpp for details on the -MM and -MT options)
%.d: %.cc
	@$(CXX) $(CXXFLAGS) $< -MM -MT $(@:.d=.o) >$@
%.o: %.cc
	$(CXX) $(CXXFLAGS) -c $< -o $@

.PHONY: clean
clean:
	rm -f $(obj) $(dep) mcclient
