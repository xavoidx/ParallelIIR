library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use work.Parallel_IIR.all;

entity block_worker is
    generic (
        L, H : positive;
        BITS : positive;
        A, D, p : positive;
        RD_LAT : positive; 
        IS_FIRST : boolean
    );
    port (

        clk, rst_n : in std_logic;

        cmd : in cmd_t;
        busy, done : out std_logic;
        
        --Memory scheduler
        load_ready : out std_logic;
        wr_L : in unsigned(BITS-1 downto 0);
        wr_H : in unsigned(BITS-1 downto 0);

        --MAP LOOKUP: For chaining together entry and exit states
        q_entry : in unsigned(BITS-1 downto 0);
        q_exit : out unsigned(BITS-1 downto 0);
        q_ok : out std_logic

        /*--REPLAY: Serial pass through the filter
        rp_entry : in unsigned(BITS-1 downto 0);
        out_data : out unsigned(BITS-1 downto 0);
        out_valid  : out std_logic;
        out_ready  : in  std_logic;
        out_last   : out std_logic*/

    );

end entity;

architecture rtl of block_worker is

    --TYPES--
    subtype data_t is unsigned(BITS-1 downto 0);
    type data_vec_t is array (natural range <>) of data_t;

    --CONSTANTS--
    constant L_addr_width : positive := clog2(L);
    constant H_addr_width : positive := clog2(H);
    constant H_start : positive := L - H;
    constant m : positive := D - A;
    signal R : positive := (D - 1) / m;
    constant u_width : positive := clog2(R + 1) + clog2(m); --2 Extra bits from multiplying by m

    --FSM SIGNALS--
    signal state, next_state : block_state := IDLE;
    signal count, next_count : integer := 0; 
    signal addr_count_r, addr_count_n : integer := 0; 

    --BUFFER LOADING SIGNALS--
    signal Lbuf_we, Lbuf_en, Hbuf_we, Hbuf_en: std_logic := '0';
    signal Hbuf1_we, Hbuf1_en : std_logic := '0';
    signal Hbuf2_we, Hbuf2_en : std_logic := '0'; --Only for first block
    signal Hbuf1_rdata, Hbuf2_rdata : data_t; 
    signal Hbuf_demux_r, Hbuf_demux_n : std_logic := '0';
    signal Lbuf_raddr, Lbuf_waddr : unsigned(L_addr_width-1 downto 0);
    signal Hbuf_raddr, Hbuf_waddr : unsigned(H_addr_width-1 downto 0); 
    signal Hbuf_rdata, Lbuf_rdata : data_t; 

    constant smin : data_t := (others => '0');
    constant smax : data_t := (others => '1');
    signal s_n, s_r : data_t := (others => '0');
    
    --SERIAL EXECUTOR SIGNALS--
    signal SE_s_entry, SE_s_out, SE_x_in : data_vec_t(0 to 1); 
    signal SE_in_valid, SE_ld, SE_en, SE_rst_n, SE_out_valid : std_logic_vector(1 downto 0); 
    signal SE_r : unsigned(clog2(D)-1 downto 0); 

    --TABLE BUILDING SIGNALS--
    signal l_n, l_r, h_n, h_r : data_t;
    signal rd_valid_sr_n, rd_valid_sr_r  : std_logic_vector(RD_LAT-1 downto 0) := (others => '0');
    signal rd_issue : std_logic := '0';
    signal table_ok_n, table_ok_r : std_logic := '0';
    type offset_map_t is array (0 to R-1) of unsigned(u_width-1 downto 0);
    signal offset_map_n, offset_map_r : offset_map_t := (others => (others => '0'));
    
    --TABLE READ SIGNALS--
    signal q_exit_n, q_exit_r : data_t := (others => '0'); 
    signal q_ok_n, q_ok_r : std_logic := '0';

    --RESET MAP--
    function init_table return offset_map_t is
        variable result : offset_map_t;
    begin
        for i in 1 to result'length loop
            result(i-1) := to_unsigned(m*i, result(i-1)'length);
        end loop;
        return result;
        end function; 
        
    constant RESET_MAP : offset_map_t := init_table;

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
            waddr => Lbuf_waddr, 
            raddr => Lbuf_raddr, 
            wdata => wr_L,
            rdata => Lbuf_rdata
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
            waddr => Hbuf_waddr,
            raddr => Hbuf_raddr,
            wdata => wr_H,
            rdata => Hbuf1_rdata
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
            waddr => Hbuf_waddr,
            raddr => Hbuf_raddr,
            wdata => wr_H,
            rdata => Hbuf2_rdata
        ); 
    end generate; 

    process(Hbuf_demux_r, Hbuf_en, Hbuf_we, Hbuf1_rdata, Hbuf2_rdata) begin
        if IS_FIRST = true then
            if Hbuf_demux_r = '0' then
                Hbuf1_en <= Hbuf_en;
                Hbuf1_we <= Hbuf_we;
                Hbuf_rdata <= Hbuf1_rdata; 
            else
                Hbuf2_en <= Hbuf_en;
                Hbuf2_we <= Hbuf_we;
                Hbuf_rdata <= Hbuf2_rdata; 
            end if;
        else
            Hbuf1_en <= Hbuf_en;
            Hbuf1_we <= Hbuf_we;
            Hbuf_rdata <= Hbuf1_rdata; 
        end if;
    end process;

    SE0 : entity work.serial_executor
        generic map (
            A => A, Dlog2 => clog2(D), BITS => BITS, p => p
        )
        port map (
            clk => clk, s_entry => SE_s_entry(0), x_in => SE_x_in(0),
            in_valid => SE_in_valid(0), ld => SE_ld(0), en => SE_en(0), rst_n => SE_rst_n(0),
            s_out => SE_s_out(0), out_valid => SE_out_valid(0), r => SE_r
        );

    SE1 : entity work.serial_executor
        generic map (
            A => A, Dlog2 => clog2(D), BITS => BITS, p => p
        )
        port map (
            clk => clk, s_entry => SE_s_entry(1), x_in => SE_x_in(1),
            in_valid => SE_in_valid(1), ld => SE_ld(1), en => SE_en(1), rst_n => SE_rst_n(1),
            s_out => SE_s_out(1), out_valid => SE_out_valid(1), r => open
        );

    process(all) 
        variable q_ok_v : boolean := false;
    begin

        --DEFAULTS--
        --out_valid <= '0';
        --out_last <= '0'; 
        --out_data <= (others => '0');
        --q_exit <= (others => '0');
        q_ok <= '0';
        busy <= '0'; done <= '0';
        load_ready <= '0';

        --BUFFER DEFAULTS--
        Lbuf_we <= '0'; Lbuf_en <= '0'; Hbuf_we <= '0'; Hbuf_en <= '0';
        Hbuf_demux_n <= Hbuf_demux_r;

        --SE DEFAULTS--
        SE_rst_n <= (others => '0'); SE_en <= (others => '0'); SE_ld <= (others => '0'); SE_in_valid <= (others => '0');
        
        --MAP BUILDING DEFAULTS--
        h_n <= h_r; l_n <= l_r;
        offset_map_n <= offset_map_r;
        table_ok_n <= table_ok_r;
        q_ok_n <= q_ok_r;

        q_ok_v := (table_ok_n = '1') and (q_entry >= l_r) and (q_entry <= l_r + R);
        q_ok_n <= '1' when q_ok_v else '0';
        q_exit_n <= (others => '0');
        if q_ok_v then
            q_exit_n <= resize((offset_map_r(to_integer(q_entry - l_r - 1)) / m), l_r'length) + l_r;
        end if; 
        q_ok <= q_ok_r;
        q_exit <= q_exit_r; 

        case state is
            --Cmd pulse interpretter
            when IDLE =>
                busy <= '0'; 
                done <= '1';
                case cmd is
                    when LOAD =>
                        next_state <= LOAD;
                        next_count <= 0;
                        addr_count_n <= 0;
                        table_ok_n <= '0';
                    when REPLAY =>
                        next_state <= REPLAY;
                        next_count <= 0;
                        addr_count_n <= 0;
                    when BUILD =>
                        --RESET THE SHARED BASE RANK TABLE--
                        offset_map_n <= reset_map;
                        Hbuf_demux_n <= not Hbuf_demux_r;
                        next_state <= BUILD_CERT;
                        next_count <= 0;
                        addr_count_n <= 0;
                        table_ok_n <= '0';
                    when others => null;
                end case;

            when LOAD =>
                done <= '0';
                busy <= '1'; 
                --Attach L_waddr TO count
                Lbuf_waddr <= to_unsigned(addr_count_r, L_addr_width); 
                Lbuf_we <= '1'; 
                
                --Attach H_waddr to count + H - L
                if count + H - L >= 0 then
                    Hbuf_waddr <= to_unsigned(addr_count_r + H - L, H_addr_width); 
                end if;
                --Begin transmitting samples from mem_scheduler
                load_ready <= '1';

                if count < H_start then
                    next_count <= count + 1;
                    addr_count_n <= addr_count_r + 1; 
                    next_state <= LOAD;
                elsif count < L then 
                    next_count <= count + 1;
                    addr_count_n <= addr_count_r + 1; 
                    next_state <= LOAD;
                    Hbuf_we <= '1'; 
                elsif count = L then
                    load_ready <= '0';
                    Lbuf_we <= '0'; 
                    Hbuf_we <= '0'; 
                    next_state <= IDLE;
                end if;

            when BUILD_CERT =>
                done <= '0';
                busy <= '1'; 
                SE_x_in(0) <= Hbuf_rdata;
                SE_x_in(1) <= Hbuf_rdata;
                Hbuf_raddr <= to_unsigned(addr_count_r, H_addr_width);
                SE_rst_n <= (others => '1'); 

                addr_count_n <= addr_count_r + 1 when addr_count_r < H - 1 else addr_count_r;  
                rd_issue <= '1' when addr_count_r < H - 1 else '0';
                rd_valid_sr_n <= rd_valid_sr_r(RD_LAT-2 downto 0) & rd_issue;
                Hbuf_en <= '1';
                SE_in_valid <= (others => rd_valid_sr_r(RD_LAT-1)); 
                    
                SE_s_entry(0) <= smin;
                SE_s_entry(1) <= smax; 
                SE_en <= (others => '1');
                SE_ld <= (others => '1') when count = 0 else (others => '0');
                next_count <= 1;
                l_n <= SE_s_out(0) when SE_out_valid(0) = '1' else l_r;
                h_n <= SE_s_out(1) when SE_out_valid(1) = '1' else h_r;

                if (rd_issue = '0') and
                        (SE_out_valid = (SE_out_valid'range => '0')) and
                        (rd_valid_sr_r = (rd_valid_sr_r'range => '0')) then
                    next_state <= BUILD_TABLE;
                    addr_count_n <= 0;
                    next_count <= 0;        
                else
                    next_state <= BUILD_CERT;
                end if; 

            when BUILD_TABLE =>
                done <= '0';
                busy <= '1'; 

                --ISSUE READS TO L-BUFFER--
                SE_x_in(0) <= Lbuf_rdata;
                Lbuf_raddr <= to_unsigned(addr_count_r, L_addr_width);
                SE_rst_n(0) <= '1'; 
                addr_count_n <= addr_count_r + 1 when addr_count_r < L - 1 else addr_count_r;  
                rd_issue <= '1' when addr_count_r < L - 1 else '0';

                rd_valid_sr_n <= rd_valid_sr_r(RD_LAT-2 downto 0) & rd_issue;
                Lbuf_en <= '1';
                SE_in_valid(0) <= rd_valid_sr_r(RD_LAT-1); 
                SE_en(0) <= '1';

                if SE_out_valid(0) = '1' then
                    table_lanes : for i in 0 to R-1 loop
                        offset_map_n(i) <= offset_map_r(i) - m when
                            SE_r < offset_map_r(i) else offset_map_r(i); 
                    end loop;
                end if;
                
                if (rd_issue = '0') and
                        (SE_out_valid = (SE_out_valid'range => '0')) and
                        (rd_valid_sr_r = (rd_valid_sr_r'range => '0')) then
                    next_state <= IDLE;
                    table_ok_n <= '1';
                    addr_count_n <= 0;
                    next_count <= 0;        
                else
                    next_state <= BUILD_TABLE;
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
                addr_count_r <= addr_count_n;
                Hbuf_demux_r <= Hbuf_demux_n;
                rd_valid_sr_r <= rd_valid_sr_n;
                offset_map_r <= offset_map_n;
                table_ok_r <= table_ok_n;
                s_r <= s_n;
                l_r <= l_n;
                h_r <= h_n;
                q_exit_r <= q_exit_n;
                q_ok_r <= q_ok_n;
            end if;
        end if; 
    end process;
    
end architecture rtl;
