package Parallel_IIR is
    type input_block is array (natural range <>) of signed;
end package;

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.Parallel_IIR.all

entity block is
    generic (
        L : positive;
        bit_depth : positive
    );
    port (
        
        ld, rst_n : in std_logic;
        inputs : in input_block(0 to L)(bit_depth-1 downto 0);

        K_en : in std_logic; --Pulled high to start K backward pass phase
        K_ready : out std_logic; --Kmap ready
        
        serial_en : in std_logic; --Puts block into serial pass mode
        in_state : in signed(bit_depth-1 downto 0); --Starting state for serial pass
        out_state : out signed(bit_depth-1 downto 0); --Live computations during a serial pass
        out_valid, out_final : out std_logic --Out_final asserted at the end of a serial pass. Out_state has final state on it 
    );

end entity;