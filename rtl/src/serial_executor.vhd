library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

entity serial_executor is
    generic (
        A, Dlog2, p : positive;
        BITS : positive 
    );
    port (
        clk : in std_logic;
        s_entry : in unsigned(BITS-1 downto 0); 
        x_in : in unsigned(BITS-1 downto 0); 
        in_valid : in std_logic;
        ld, en, rst_n : in std_logic;
        s_out : out unsigned(BITS-1 downto 0) := (others => '0'); 
        out_valid: out std_logic := '0'
    );
end entity;

architecture rtl of serial_executor is
    signal acc : unsigned(BITS-1 downto 0);
    signal c : unsigned(BITS+Dlog2-1 downto 0);
    signal c_valid : std_logic := '0';
    constant D : positive := 2**Dlog2; 
    constant m : positive := D - A;
begin
    process(clk) begin
        if(rising_edge(clk)) then
            if rst_n = '0' then
                acc <= (others => '0');
            else
                if en = '1' then
                    if ld = '1' then
                        acc <= s_entry;
                        out_valid <= '0';
                    else    
                        c <= to_unsigned(m, Dlog2) * x_in + to_unsigned(p, Dlog2);
                        c_valid <= in_valid;
                        if c_valid = '1' then
                            acc <= shift_right(to_unsigned(A, Dlog2) * acc + c, Dlog2)(BITS-1 downto 0);
                            out_valid <= '1';
                        end if;
                    end if;
                end if;
            end if;
        end if;
    end process;
    s_out <= acc;
end architecture rtl;