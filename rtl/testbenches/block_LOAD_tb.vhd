library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.Parallel_IIR.all;
use std.env.all;

entity block_LOAD_tb is
end entity;

architecture rtl of block_LOAD_tb is
    
    constant L : positive := 10;
    constant H : positive := 8;
    constant A : positive := 61;
    constant D : positive := 64;
    constant p : positive := D / 2;
    constant RD_LAT : positive := 2; 
    constant BITS : positive := 4;
    constant IS_FIRST : boolean := false; 
    signal clk : std_logic := '0';
    signal cmd : cmd_t := NONE;
    signal wr_L : unsigned(BITS-1 downto 0);
    signal wr_H : unsigned(BITS-1 downto 0);
    signal load_ready : std_logic;
    signal idx : integer := 6;
    signal done : std_logic;
    signal q_entry : unsigned(BITS-1 downto 0);
    type test_samples_t is array (natural range <>) of unsigned(BITS-1 downto 0);
    constant test_samples : test_samples_t := (
        x"0", x"1", x"2", x"3", x"4", x"5", x"6", x"7", x"8", x"9", x"A", x"B", x"C", x"D", x"E", x"F"
    );

begin

    block_worker_dut : entity work.block_worker
        generic map (
            L => L,
            H => H,
            A => A,
            D => D,
            p => p,
            RD_LAT => RD_LAT,
            BITS => BITS,
            IS_FIRST => IS_FIRST
        )
        port map (
            clk => clk,
            rst_n => '1',
            load_ready => load_ready,
            wr_L => wr_L,
            wr_H => wr_H,
            done => done,
            cmd => cmd,
            q_entry => q_entry,
            q_exit => open,
            q_ok => open
        );

    clk <= not clk after 5 ns;
    wr_L <= test_samples(idx mod test_samples'length);
    wr_H <= test_samples(idx mod test_samples'length);

    process(clk) begin
        if rising_edge(clk) then
            if load_ready = '1' then
                idx <= idx + 1;
            end if;
        end if;
    end process;

    process begin
        
        wait until rising_edge(clk);

        --ISSUE LOAD CMD--
        if done = '1' then
            cmd <= LOAD;
        end if; 
        wait until done = '0';
        cmd <= NONE;
        wait until done = '1';
        
        --ISSUE BUILD CMD--
        if done = '1' then
            cmd <= BUILD;
        end if; 
        wait until done = '0';
        cmd <= NONE;
        wait until done = '1';

        q_entry <= x"8";
        wait until rising_edge(clk);

        wait until rising_edge(clk);
        report "simulation ended successfully";
        finish;
        
    end process;

    
end architecture rtl;
