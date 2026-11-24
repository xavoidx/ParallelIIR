STD := --std=08
GHDL := ghdl
BUILD := build
WAVES := waves
VHDL := sample_buf serial_executor block_worker 
VHDL_PACKAGES := parallel_iir
SRCS := $(foreach file, $(VHDL), src/$(file).vhd)
PACKAGES := $(foreach file, $(VHDL_PACKAGES), packages/$(file).vhd)
LOAD_TB_SRCS := testbenches/block_LOAD_tb.vhd 
SERIAL_EXECUTOR_TB_SRCS := testbenches/serial_executor_tb.vhd


.PHONY : block_load_tb clean 

$(BUILD): 
	mkdir -p $@

$(WAVES):
	mkdir -p $@

block_load_tb : $(BUILD)/block_load_tb \
	| $(BUILD) $(WAVES)
	$(BUILD)/$@ --stop-time=600ns --wave=$(WAVES)/$@.ghw

$(BUILD)/block_load_tb : $(PACKAGES) $(SRCS) $(LOAD_TB_SRCS) | $(BUILD)
	$(GHDL) -i $(STD) --workdir=$(BUILD) $^
	$(GHDL) -m $(STD) --workdir=$(BUILD) -o $@ $(notdir $@)

serial_executor_tb : $(BUILD)/serial_executor_tb \
	| $(BUILD) $(WAVES)
	$(BUILD)/$@ --stop-time=10us --wave=$(WAVES)/$@.ghw
	
$(BUILD)/serial_executor_tb : $(PACKAGES) $(SRCS) $(SERIAL_EXECUTOR_TB_SRCS) | $(BUILD)
	$(GHDL) -i $(STD) --workdir=$(BUILD) $^
	$(GHDL) -m $(STD) --workdir=$(BUILD) -o $@ $(notdir $@)

clean :
	rm -rf $(BUILD)
