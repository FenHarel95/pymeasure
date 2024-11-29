from sys import prefix

from pymeasure.instruments import Channel, Instrument, SCPIMixin
from pymeasure.instruments.validators import strict_discrete_set, strict_range

############### Imports for testing
from string import Template


class VNAChannel(Channel):
    """A channel ch for the VNA."""

    power = Channel.control(
        "SOUR{ch}:POW?", "SOUR{ch}:POW %d",
        """Control the power of the internal signal source in dBm""",
        validator=strict_range,
        values=[-40, 10],
        dynamic=True,
    )

    if_bandwidth = Channel.control(
        "SENS{ch}:BAND?", "SENS{ch}:BAND %d",
        """Control the IF bandwidth resolution in Hz. Limits to be checked""",
        cast=int,
        validator=strict_range,
        values=[1, 1e6],
        dynamic=True,
    )

    selective_bandwidth = Channel.control(
        "SENS{ch}:BAND:DRED?", "SENS{ch}:BAND:DRED %s",
        """Control the activation of dynamic bandwidth reduction at low frequencies.,

        ====== =======
        Value  Meaning
        ====== =======
        False  IF bandwidth is constant for all frequencies (faster sweep, less accurate). 
        True   IF bandwidth is reduced at low frequencies (slower sweep, more accurate)
        ====== =======
        """,
        validator=strict_discrete_set,
        values={False: "OFF", True: "ON"},
        map_values=True,
    )

    sweep_continuity = Channel.control(
        "INIT{ch}:CONT?", "INIT{ch}:CONT %s",
        """Control whether the analyzer measures in single sweep or in continuous sweep mode.,

        ====== =======
        Value  Meaning
        ====== =======
        False  The measurement is stopped after the number of sweeps defined via sweep_number 
        True   The analyzer measures continuously, repeating the current sweep.
        ====== =======
        """,
        validator=strict_discrete_set,
        values={False: "OFF", True: "ON"},
        map_values=True,
    )

    sweep_number = Channel.control(
        "SENS{ch}:SWE:COUN?", "SENS{ch}:SWE:COUN %d",
        """Control the number of sweeps to be performed in single sweep mode (sweep_continuity=False).""",
        cast=int,
        validator=strict_range,
        values=[1, 999],
        dynamic=True,
    )

    sweep_counter = Channel.measurement(
        "CALC{ch}:DATA:NSW:COUN?",
        """Measures the calculated minimum duration of the sweep (depends on the other channel settings). 
        We assume the default setting [SENSe<Ch>:]SWEep:TIME:AUTO.""",
    )

    scope_single_sweep = Channel.control(
        "INIT:IMM:SCOP?", "INIT:IMM:SCOP %s",
        """Control the scope (channels) of the single sweep.,

        ====== =======
        Value  Meaning
        ====== =======
        False  The single sweep performed by launch_single_sweep is performed in all channels. {ch} prefix is ignored 
               by analyzer.
        True   The single sweep performed by launch_single_sweep is for the active channel only.
        ====== =======
        """,
        validator=strict_discrete_set,
        values={False: "ALL", True: "SING"},
        map_values=True,
    )

    def launch_single_sweep(self):
        """Function that launches a new single sweep sequence, according to scope_single sweep."""
        ans = self.write("INIT{ch}:IMM; *OPC")
        #return ans

    sweep_points = Channel.control(
        "SENS{ch}:SWE:POIN?", "SENS{ch}:SWE:POIN %d",
        """Control the total number of measurement points per sweep (Number of Points).""",
        cast=int,
        validator=strict_range,
        values=[1, 60001],
        dynamic=True,
    )

    sweep_time = Channel.measurement(
        "SEN{ch}:SWE:TIME?",
        """Measures the calculated minimum duration of the sweep (depends on the other channel settings). 
        We assume the default setting [SENSe<Ch>:]SWEep:TIME:AUTO.""",
    )

    sweep_type = Channel.control(
        "SENSe{ch}:SWEep:TYPE?", "SENSe{ch}:SWEep:TYPE %s",
        """Control the sweep type variable (frequency/power/time).
        
        ====== =======
        Value  Meaning
        ====== =======
        LIN    Lin. frequency sweep at constant source power.
        SEG    Segmented frequency sweep. The sweep range is composed of several ranges see SENS:SEGM<Seg>... subsystem.
        POW    Power sweep. The measurement is performed at constant frequency but with variable generator power.
        POIN   CW Mode sweep, time sweep triggered according to the current trigger settings.
        See user manual for the other types (pg. 976).
        ====== =======
        """,
        validator=strict_discrete_set,
        values=["LIN", "SEG", "POW", "POIN", "LOG", "CW", "PUL", "IAMP", "IPH"],
        dynamic=True,
    )

    cw_frequency = Channel.control(
        "SENS{ch}:FREQ:CW?", "SENS{ch}:FREQ:CW %d",
        """Control the CW (Continuous Wave) frequency in GHz for fixed frequency sweep.
        """,
        validator=strict_range,
        values=[0.01, 50],
        dynamic=True,
        set_process=lambda v: 1e9 * v,  # convert frequency to Hz
    )

    avg_active = Channel.control(
        "SENSe{ch}:AVER:STAT?", "SENSe{ch}:AVER:STAT %s",
        """Control the activation of the sweep average.,

        ====== =======
        Value  Meaning
        ====== =======
        False  Average is deactivated.
        True   Average is on.
        ====== =======
        """,
        validator=strict_discrete_set,
        values={False: "OFF", True: "ON"},
        map_values=True,
    )

    avg_number = Channel.control(
        "SENS{ch}:AVER:COUN?", "SENS{ch}:AVER:COUN %d",
        """Control number of consecutive sweeps to be combined for the sweep average.""",
        cast=int,
        validator=strict_range,
        values=[1, sweep_number],
        dynamic=True,
    )

    avg_counter = Instrument.measurement(
        "SENS{ch}:AVER:COUN:CURR?",
        """Measure the number of the sweep which is currently measured.""",
    )

    def clear_avg(self):
        """Functions that clears any previous averaging, restarting the process."""
        message = "SENSe{ch}:AVER:CLE"
        self.write(message)

    freq_start = Channel.control(
        "SENS{ch}:FREQ:STAR?", "SENS{ch}:FREQ:STAR %d",
        """Control the start frequency in GHz for frequency sweeps.""",
        validator=strict_range,
        values=[0.01, 50],
        dynamic=True,
        set_process=lambda v: 1e9 * v,  # convert frequency to Hz
        get_process=lambda v: 1e-9 * v,  # convert frequency to GHz
    )

    freq_stop = Channel.control(
        "SENS{ch}:FREQ:STOP?", "SENS{ch}:FREQ:STOP %d",
        """Control the stop frequency in GHz for frequency sweeps.""",
        validator=strict_range,
        values=[0.01, 50],
        dynamic=True,
        set_process=lambda v: 1e9 * v,  # convert frequency to Hz
        get_process=lambda v: 1e-9 * v,  # convert frequency to GHz
    )

    meas_ports = Channel.setting(
        "CALC{ch}:PAR:DEF:SGR %s",
        """Control the number of S-parameter-traces corresponding to the number of ports.

        ====== =======
        Value  Meaning
        ====== =======
        1      For measurements with port 2 only.
        2      For measurements with port 2 only.
        1,2    For measurements with ports 1,2.
        ====== =======
        """,
        validator=strict_discrete_set,
        values=["1", "2", "1,2"],
        dynamic=True,
    )

    meas_traces = Channel.measurement(
        "CALC{ch}:DATA:SGR?",
        """Measures the number of S-parameter-traces available for measurements.
        One must first Define the ports with meas_ports
        """
    )

    meas_xaxis_values = Channel.measurement(
        "CALC{ch}:DATA:STIM?",
        """Measures the values of the stimulus values, i.e. the x-axis values of the sweep.
        """
    )


    trigger_sequence = Channel.control(
        "TRIG{ch}:SEQ:LINK?", "TRIG{ch}:SEQ:LINK %s",
        """Control the triggered measurement sequence.

        ====== =======
        Value  Meaning
        ====== =======
        SWE    Trigger event starts an entire sweep.
        SEG    Trigger event starts a sweep segment, if segmented frequency sweep is active i.e. if sweep_type = SEG.
        POIN   Trigger event starts measurement at the next sweep point.
        PPO    Trigger event starts the next partial measurement at the current or at the next sweep point.
        ====== =======
        """,
        validator=strict_discrete_set,
        values=["SWE", "SEG", "POIN", "PPO"],
        dynamic=True
    )

    trigger_source = Channel.control(
        "TRIG{ch}:SEQ:SOUR?", "TRIG{ch}:SEQ:SOUR %s",
        """Control the source for the events that the analyzer uses to start a measurement sequence.

        ====== =======
        Value  Meaning
        ====== =======
        IMM    Free run measurement (untriggered).
        EXT    Trigger by external signal.
        TIM    Periodic internal trigger signal. The period of the timer is controlled by 
        MAN    Trigger event generated by pressing the Manual Trigger softkey.
        PGEN   Trigger event generated the pulse generator (see manual pg. 1092).
        ====== =======
        """,
        validator=strict_discrete_set,
        values=["IMM", "EXT", "TIM", "MAN", "PGEN"],
        dynamic=True,
    )

    trigger_timer = Channel.control(
        "TRIG{ch}:SEQ:TIM?", "TRIG{ch}:SEQ:TIM %d",
        """Control the period in ms of the internal periodic signal that can be used as a 
        trigger source (trigger_source = TIM).""",
        validator=strict_range,
        values=[0.01, 13680000],
        dynamic=True,
        set_process=lambda v: 1e-3 * v,  # convert time to s
    )


    def define_default_traces(self, measurements: list):
        """Function that defines a set of four traces to measure the scattering matrix Sij between ports i qnd j."""
        traces_number = len(measurements)
        traces_list = list(range(1, traces_number + 1))
        traces_id_list = []
        for i in traces_list:
            traces_id_list.append(str(self.id) + "_" + str(i) )
            self.add_child(VNAChannel.ChannelTrace, traces_id_list[i-1], prefix="tr_") # creating pymeasure "traces"
            self.create_zva_trace(traces_id_list[i-1], measurements[i-1])  # defining associated real ZVA traces

    def create_zva_trace(self, trc_id, measurement):
        """Function that creates a trace with a given name for a specified measurement.
        The measurement typically should be "Sij", "Zij", etc. where i,j=1,2,...
        See pgs. 678-680 in manual for more measurements
        """
        message = "CALC{ch}:PAR:SDEF " + "'Trc" + trc_id + "', " + "'" + measurement + "'"
        self.write(message)

    class ChannelTrace(Channel):
        """A trace tr for the channel ch of the VNA."""
        placeholder = "tr"  # changes the default placeholder to differentiate it from parent class

        measurement = Channel.control(
            "CALC{{ch}}:PAR:MEAS? 'Trc{tr}'", "CALC{{ch}}:PAR:MEAS 'Trc{tr}', '%s'",
            """Control the measurement assigned to the trace. 
            Note that the default is Sij when creating a trace, see create_trace function.

            ====== =======
            Value  Meaning
            ====== =======
            Sij    S-matrix (scattering matrix) elements (i,j=1,2,...).
            Z-Sij  Z-matrix (matched-circuit impedances) elements (i,j=1,2,...).
            see manual (pg. 678-680) for additional possible measurements.
            ====== =======
            """,
            validator=strict_discrete_set,
            values=["S11", "S12", "S21", "S22", "Z-S11", "Z-S12", "Z-S21", "Z-S22"],
            dynamic=True
        )

        format = Channel.control(
            "CALC{{ch}}:PAR:SEL 'Trc{tr}'; :CALC{{ch}}:FORM?",
            "CALC{{ch}}:PAR:SEL 'Trc{tr}'; :CALC{{ch}}:FORM %s",
            """Control the format of the trace.
            Assume that the result at a sweep point is given by the complex quantity z = x + jy.
            Always change format before measuring. 

            ====== =======
            Value  Meaning
            ====== =======
            MLIN   Calculate the magnitude of z, to be displayed in a Cartesian diagram with a linear scale.
            MLOG   Calculate the magnitude of z, displayed in a Cartesian diagram with a logarithmic scale.
            UPH    Unwrapped phase of z, displayed in a Cartesian diagram with a linear vertical axis.
            PHAS   Phase of z, displayed in a Cartesian diagram with a linear vertical axis.
            SMIT   Magnitude and phase, displayed in a Smith chart.
            REAL   Real part (x), displayed in a Cartesian diagram.
            IMAG   Imaginary part (y), displayed in a Cartesian diagram.
            see manual (pg. 629) for the other formats.
            ====== =======
            """,
            validator=strict_discrete_set,
            values=["MLIN", "MLOG", "UPH", "PHAS", "SMIT", "REAL", "IMAG", "POL", "ISM", "GDEL", "SWR"],
            dynamic=True
        )

        data_raw = Channel.measurement(
            "CALC{{ch}}:PAR:SEL 'Trc{tr}'; :CALC:DATA? SDAT; *WAI",
            """Measure the real and imaginary part of each measurement point. 2 values per trace point 
                        irrespective of tr_format."""
        )

        data_formated = Channel.measurement(
            "CALC{{ch}}:PAR:SEL 'Trc{tr}'; :CALC:DATA? FDAT; *WAI",
            """Measure the data of the trace according to tr_format. Single value for every measurement point."""
        )

        def assign_trace_to_window(self, wnd: str):
            """Function that assigns a given trace {tr} to a window wnd"""
            message = "DISP:WIND" + wnd + ":TRAC:EFE 'Trc{tr}'"
            self.write(message)

    def single_sweep_vna(self, sweeps, control=None, idn=None):
        count = 0
        count2 = -1
        self.clear_avg()
        self.launch_single_sweep()
        while self.sweep_counter < sweeps:
            count = int(self.sweep_counter)
            if (count == (count2 + 1)) and (control == True):
                print(idn + " Freq. sweeps done:" + str(count))
                count2 = count
        if control:
            print(idn + " Freq. sweeps done:" + str(int(self.sweep_counter)))


class ZVA(SCPIMixin, Instrument):
    """ Represents the Rohde&Schwarz ZVA vector network analyzer
    interface for interacting with the instrument.
    """

    def __init__(self, adapter: str , name: str, **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )


    def define_default_channels(self, channel_number: int):
        """Function that defines channel_number of new pymeqsure channels and assigns them to corresponding
        ZVA channels."""
        while channel_number < 1:
            print("For " + self.name + " the number of channels must be at least 1.")
            channel_number = int(input("Please enter a valid number of channels: "))

        channels_list = list(range(1, channel_number + 1))

        for channel in channels_list:
            self.add_child(VNAChannel, channel) # creating pymeasure channels
            self.create_zva_channel(channel)  # defining associated real ZVA channels

    def create_zva_channel(self, numb):
        """Function that creates a channel with number numb>1. Channel name is Ch{numb}."""
        numb= str(numb)
        message = "CONF:CHAN" + numb + ":STAT ON"
        self.write(message)
        print("Ch" + numb + " created.")

    def delete_zva_channel(self, numb):
        """Function that deletes channel with number numb>1 (Ch{numb})."""
        numb = str(numb)
        message = "CONF:CHAN" + numb + ":STAT OFF"
        self.write(message)
        print("Ch" + numb + " deleted.")

    def create_window(self, numb):
        """Function that creates a window with number numb>1."""
        numb = str(numb)
        message = "DISP:WIND" + numb + ":STAT ON"
        self.write(message)
        print("Window " + numb + " created.")

    def delete_window(self, numb):
        """Function that deletes a window with number numb>1."""
        numb = str(numb)
        message = "DISP:WIND" + numb + ":STAT OFF"
        self.write(message)
        print("Window " + numb + " deleted.")

    state = Instrument.setting(
        "MMEM:LOAD:STAT 1,%s",
        """Set the VNA state to be recalled from the given address.""",
    )

    source = Instrument.control(
        "OUTP:STAT?", "OUTP:STAT %s",
        """Control the internal source power at all ports and the power of all external generators.

        ====== =======
        Value  Meaning
        ====== =======
        OFF    Switch OFF immediately.
        ON     Switch ON immediately.
        ====== =======
        """,
        validator=strict_discrete_set,
        values=["OFF", "ON"],
    )