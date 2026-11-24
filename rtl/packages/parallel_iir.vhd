library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

package Parallel_IIR is
    type cmd_t is (REPLAY, BUILD, LOAD, NONE); --Command strobe
    type block_state is (REPLAY, BUILD_CERT, BUILD_TABLE, LOAD, IDLE);
    function clog2(n : positive) return natural;

end package;

package body Parallel_IIR is
    function clog2(n : positive) return natural is
        variable bits : natural := 0;
        variable size : positive := 1;
    begin
        while size < n loop
            size := size * 2;
            bits := bits + 1;
        end loop;
        return bits;
    end function;
end package body;
