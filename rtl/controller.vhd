library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity block_controller is
    generic ( 
        bit_depth : positive := 16;
        L : positive;
        P : positive;  
    );
    port (
        clk : in std_logic;
        data_in : in std_logic_vector(bit_depth-1 downto 0);
    );
end entity;

architecture behavioral of block_controller is
    