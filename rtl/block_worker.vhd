library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.Parallel_IIR.all;

entity block_worker is
    generic (
        L, H : positive;
        BITS : positive;
        IS_FIRST : boolean
    );
    port (

        clk, rst_n : in std_logic;

        cmd : in cmd_t;
        busy, done : out std_logic;
        
        --Memory scheduler
        load_ready : out std_logic;
        wr_L : in unsigned(BITS-1 downto 0);
        wr_H : in unsigned(BITS-1 downto 0)

        --MAP LOOKUP: For chaining together entry and exit states
       /* q_entry : in unsigned(BITS-1 downto 0);
        q_exit : out unsigned(BITS-1 downto 0);
        q_ok : out std_logic;

        --REPLAY: Serial pass through the filter
        rp_entry : in unsigned(BITS-1 downto 0);
        out_data : out unsigned(BITS-1 downto 0);
        out_valid  : out std_logic;
        out_ready  : in  std_logic;
        out_last   : out std_logic*/

    );

end entity;

architecture rtl of block_worker is
    signal state, next_state : block_state := IDLE;
    signal count, next_count : integer := 0; 
    signal Lbuf_we, Lbuf_en, Hbuf_we, Hbuf_en: std_logic := '0';
    signal Hbuf1_we, Hbuf1_en : std_logic := '0';
    signal Hbuf2_we, Hbuf2_en : std_logic := '0'; --Only for first block
    signal Hbuf_demux, next_Hbuf_demux : std_logic := '0';
    constant L_addr_width : positive := clog2(L);
    constant H_addr_width : positive := clog2(H);
    signal L_raddr, L_waddr : unsigned(L_addr_width-1 downto 0);
    signal H_raddr, H_waddr : unsigned(H_addr_width-1 downto 0); 

    constant H_start : positive := L - H;
    
begin
    
    L_buffer : entity work.sample_buf
        generic map (
            DEPTH => L,
            DATA_WIDTH => BITS
        )
        port map (
            clk => clk,
            we => Lbuf_we,
            en => Lbuf_en,
            waddr => L_waddr, 
            raddr => L_raddr, 
            wdata => wr_L
            -- ... --
        );

    H_buffer : entity work.sample_buf
        generic map (
            DEPTH => H,
            DATA_WIDTH => BITS
        )
        port map (
            clk => clk,
            we => Hbuf1_we,
            en => Hbuf1_en,
            waddr => H_waddr,
            raddr => H_raddr,
            wdata => wr_H
            -- ... --
        );
    
    --The first block has a second H-buffer so it can store 
    --the rail of the last block for the next set of inputs.
    --The Hbuf_we and Hbuf_en have to be demuxed to the proper
    --buffer for the first block.
    Hbuf2 : if IS_FIRST = true generate
        H_buffer_next : entity work.sample_buf
        generic map (
            DEPTH => H,
            DATA_WIDTH => BITS
        )
        port map (
            clk => clk,
            we => Hbuf2_we,
            en => Hbuf2_en,
            waddr => H_waddr,
            raddr => H_raddr,
            wdata => wr_H
            -- ... --
        ); 
    end generate; 

    process(Hbuf_demux, Hbuf_en, Hbuf_we) begin
        if IS_FIRST = true then
            if Hbuf_demux = '0' then
                Hbuf1_en <= Hbuf_en;
                Hbuf1_we <= Hbuf_we;
            else
                Hbuf2_en <= Hbuf_en;
                Hbuf2_we <= Hbuf_we;
            end if;
        else
            Hbuf1_en <= Hbuf_en;
            Hbuf1_we <= Hbuf_we;
        end if;
    end process;

    process(all) begin

        --DEFAULTS--
        --out_valid <= '0';
        --out_last <= '0'; 
        --out_data <= (others => '0');
        --q_exit <= (others => '0');
        --q_ok <= '0';
        busy <= '0'; done <= '0';
        load_ready <= '0';
        Lbuf_we <= '0'; Lbuf_en <= '0'; Hbuf_we <= '0'; Hbuf_en <= '0';
        case state is

            --Cmd pulse interpretter
            when IDLE =>
                busy <= '0'; 
                done <= '1';
                case cmd is
                    when LOAD =>
                        next_state <= LOAD;
                        next_count <= 0;
                    when REPLAY =>
                        next_state <= REPLAY;
                        next_count <= 0;
                    when BUILD =>
                        next_Hbuf_demux <= not Hbuf_demux;
                        next_state <= BUILD;
                        next_count <= 0;
                    when others => 
                        next_state <= state;
                end case;

            when LOAD =>
                done <= '0';
                busy <= '1'; 

                --Attach L_waddr TO couunt
                L_waddr <= to_unsigned(count, L_addr_width); 
                Lbuf_we <= '1'; 
                
                --Attach H_waddr to count + H - L
                if count + H - L >= 0 then
                    H_waddr <= to_unsigned(count + H - L, H_addr_width); 
                end if;
                --Begin transmitting samples from mem_scheduler
                load_ready <= '1';

                if count < H_start then
                    next_count <= count + 1;
                    next_state <= LOAD;
                elsif count < L then 
                        next_count <= count + 1;
                        next_state <= LOAD;
                        Hbuf_we <= '1'; 
                elsif count = L then
                        load_ready <= '0';
                        Lbuf_we <= '0'; 
                        Hbuf_we <= '0'; 
                        next_state <= IDLE;
                end if;

            when others => next_state <= IDLE; 
        end case;
    end process;

    process(clk) begin
        if(rising_edge(clk)) then
            if rst_n = '0' then
                --Reset logic
            else
                state <= next_state;
                count <= next_count;
                Hbuf_demux <= next_Hbuf_demux;
            end if;
        end if; 
    end process;
    
end architecture rtl;
