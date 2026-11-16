library IEEE;
use IEEE.std_logic_1164.all;
use work.Parallel_IIR.all;
use IEEE.numeric_std.all;

entity sample_buf is
    generic (
        DEPTH : positive;
        DATA_WIDTH : positive
    );
    port (
        clk, we, en : in std_logic;
        waddr : in unsigned(clog2(DEPTH)-1 downto 0); 
        wdata : in unsigned(DATA_WIDTH-1 downto 0);
        raddr : in unsigned(clog2(DEPTH)-1 downto 0);
        rdata : out unsigned(DATA_WIDTH-1 downto 0)
    );
end entity;

architecture rtl of sample_buf is
    type ram_t is array (0 to DEPTH-1) 
        of unsigned(DATA_WIDTH-1 downto 0);
    signal ram : ram_t;
    attribute ram_style : string;
    attribute ram_style of ram : signal is "block";
    signal r0, r1 : unsigned(DATA_WIDTH-1 downto 0);
begin
    process(clk) begin
        if rising_edge(clk) then
            if we = '1' then 
                ram(to_integer(waddr)) <= wdata;
            end if;
            if en = '1' then
                r0 <= ram(to_integer(raddr));
                r1 <= r0;
            end if;
        end if;
    end process;
    rdata <= r1;
end architecture;
