library IEEE; 
use IEEE.numeric_std.all;
use IEEE.std_logic_1164.all;
use work.Parallel_IIR.all;
use std.env.all;

entity serial_executor_tb is
end entity;

architecture rtl of serial_executor_tb is
    constant A : positive := 61;
    constant D : positive := 64;
    constant Dlog2 : positive := clog2(D);
    constant BITS : positive := 16; 
    constant p : positive := D / 2; 
    
    type input_array is array (natural range <>) of unsigned(BITS-1 downto 0);
    constant inputs : input_array := (
        x"0401", x"0402", x"0403", x"0404", x"0405", x"0406", x"0407", x"0408"
    ); 
    constant entry_state : unsigned(BITS-1 downto 0) := x"0010"; 
    
    signal clk : std_logic := '0';
    signal s_entry : unsigned(BITS-1 downto 0); 
    signal x_in : unsigned(BITS-1 downto 0);
    signal in_valid : std_logic;
    signal ld, en, rst_n : std_logic := '0';
    signal s_out : unsigned(BITS-1 downto 0) := (others => '0'); 
    signal out_valid: std_logic;
    signal counter : integer := 0;
begin
    serial_executor_dut : entity work.serial_executor
        generic map (
            A => A, Dlog2 => Dlog2, BITS => BITS, p => p
        )
        port map (
            clk => clk, s_entry => s_entry, x_in => x_in,
            in_valid => in_valid, ld => ld, en => en, rst_n => rst_n,
            s_out => s_out, out_valid => out_valid
        );
    clk <= not clk after 5 ns; 
    process begin

        rst_n <= '0';
        wait until rising_edge(clk);
        
        rst_n <= '1';
        en <= '1';
        ld <= '1';
        s_entry <= entry_state; 
        wait until rising_edge(clk);

        assert (out_valid = '0') 
            report "ERROR: Out_valid not set to 0 after loading entry state"
            severity error;

        while counter < inputs'length loop
            ld <= '0';
            in_valid <= '1';
            x_in <= inputs(counter);
            counter <= counter + 1;
            
            wait until rising_edge(clk);
        end loop;
        in_valid <= '0';
        wait until rising_edge(clk);
        wait until rising_edge(clk);
        wait until rising_edge(clk);
        wait until rising_edge(clk);
        
        report "Simulation ended successfully";
        finish;
    end process;
    
end architecture rtl;