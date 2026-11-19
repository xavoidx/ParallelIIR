library library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use std.textio.all;
use IEEE.std_logic_textio.all;

type sample_dist is array (natural range <>) of unsigned;

entity mem_scheduler is
    generic (
        P, BITS : positive
    );
    port (
        file input_file : text; 
        L_out : sample_dist(0 to P-1)(BITS-1 downto 0);
        clk, en : in std_logic
    );
end entity;

architecture rtl of mem_scheduler is
begin
    
    process(clk)
        file input_file : text open read_mode is "input.txt";
        variable input_line : line;
        variable input_value : unsigned(BITS-1 downto 0);
    begin
        if rising_edge(clk) then
            for i in 0 to P-1 loop
                L_out(i) <= (others => '0');
            end loop;
            if en = '1' then
                for i in 0 to P-1 loop
                    if not endfile(input_file) then
                        readline(input_file, input_line)
                        read(input_line, input_value);
                        L_out(i) <= input_value;
                    end if;
                end loop;
        end if; 
        
end architecture rtl;