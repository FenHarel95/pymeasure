from cytoolz import interpose
from pymeasure.instruments import Instrument, SCPIMixin
from pymeasure.instruments.validators import strict_discrete_set, \
    truncated_range

from enum import IntFlag
from string import Template

class TestErrorCode(IntFlag):
    QUARTER_SCALE_VOLTAGE_READBACK = 512
    QUARTER_SCALE_VOLTAGE = 256
    MIN_VOLTAGE_OUTPUT = 128
    MAX_VOLTAGE_OUTPUT = 64
    LOOP_BACK_TEST = 32
    DIGITAL_POT = 16
    OPTICAL_BUFFER = 8
    FLASH = 4
    RAM = 2
    ROM = 1
    OK = 0

OPERATING_MODES = ['VOLT', 'CURR']

class KepcoBOP5020(SCPIMixin, Instrument):

    _Vmax = 50
    _Imax = 20

    def __init__(self, adapter, name="Kepco BOPGL 50-20 Bipolar Power Supply", **kwargs):
        super().__init__(
            adapter=adapter,
            name=name,
            read_termination="\n",
            write_termination="\n",
            **kwargs
        )

    ################################ New
    def beep(self):
        """Cause the unit to emit a brief audible tone."""
        self.write("SYSTem:BEEP")

    confidence_test = Instrument.measurement(
        "*TST?",
        """
        Get error code after performing interface self-test procedure.

        Returns 0 if all tests passed, otherwise corresponding error code
        as detailed in manual.
        """,
        get_process=lambda v: TestErrorCode(v),
    )

    bop_test = Instrument.measurement(
        "DIAG:TST?",
        """
        Get error code after performing full power supply self-test.

        Returns 0 if all tests passed, otherwise corresponding error code
        as detailed in manual.
        Caution: Output will switch on and swing to maximum values.
        Disconnect any load before testing.
        """,
        get_process=lambda v: TestErrorCode(v),
    )

    def wait_to_continue(self):
        """ Cause the power supply to wait until all previously issued
        commands and queries are complete before executing subsequent
        commands or queries. """
        self.write("*WAI")

    voltage = Instrument.measurement(
        "MEASure:VOLTage?",
        """
        Measure voltage present across the output terminals in Volts.
        """,
        cast=float
    )

    current = Instrument.measurement(
        "MEASure:CURRent?",
        """
        Measure current through the output terminals in Amps.
        """,
        cast=float
    )

    operating_mode = Instrument.control(
        "FUNCtion:MODE?", "FUNCtion:MODE %s",
        """
        Control the operating mode of the BOP.

        As a command, a string, VOLT or CURR, is sent.
        As a query, a 0 or 1 is returned, corresponding to VOLT or CURR respectively.
        This is mapped to corresponding string.
        """,
        validator=strict_discrete_set,
        values=OPERATING_MODES,
        get_process=lambda x: OPERATING_MODES[int(x)]
    )

    current_setpoint = Instrument.control(
        "CURRent?", "CURRent %g",
        """
        Control the output current setpoint.

        Functionality depends on the operating mode.
        If power supply in current mode, this sets the output current setpoint.
        The current achieved depends on the voltage compliance and load conditions
        (see: `current`).
        If power supply in voltage mode, this sets the compliance current
        for the corresponding voltage set point.
        Query returns programmed value, meaning of which is dependent on
        power supply operating context (see: `operating_mode`).

        Output must be enabled separately (see: `output_enabled`)
        """,
        validator=truncated_range,
        values=[-1 * _Imax, _Imax]
    )

    voltage_setpoint = Instrument.control(
        "VOLTage?", "VOLTage %g",
        """
        Control the output voltage setpoint.

        Functionality depends on the operating mode.
        If power supply in voltage mode, this sets the output voltage setpoint.
        The voltage achieved depends on the current compliance and load conditions
        (see: `voltage`).
        If power supply in current mode, this sets the compliance voltage
        for the corresponding current set point.
        Query returns programmed value, meaning of which is dependent on
        power supply operating context (see: `operating_mode`).

        Output must be enabled separately (see: `output_enabled`)
        """,
        validator=truncated_range,
        values=[-1 * _Vmax, _Vmax]
    )

    ################################ End New

    output_enabled = Instrument.control(
        "OUTPut?",
        "OUTP:CONT OFF; OUTPut %d",
        """
        Control whether the source is enabled, takes values True or False (bool)
        """,
        validator=strict_discrete_set,
        values={True: 1, False: 0},
        map_values=True,
    )

    output_mode = Instrument.control(
        "OUTP:MODE?",
        "OUTP:MODE %s",
        """
        Control the source of the trigger events
        
        ======      =======
        Value       Meaning
        ======      =======
        ACTIVE      See manual pg. 3-10.
        RESISTIVE   See manual pg. 3-10.
        BATTERY     See manual pg. 3-10.
        ====== =======
        """,
        validator=strict_discrete_set,
        values={"ACTIVE", "RESISTIVE", "BATTERY"},
    )

    trigger_source = Instrument.control(
        "TRIG:SOUR?",
        "TRIG:SOUR %s",
        """
        Control the source of the trigger events
        
        ====== =======
        Value  Meaning
        ====== =======
        BUS    A trigger event is created by sending either *TRG or GPIB <GET> commands.
        EXT    The trigger is created by connecting the external trigger line (see manual.)
        IMM    Controls trigger_voltage or trigger_current immediately program the output, regardless of trigger arming.
        ====== =======
        """,
        validator=strict_discrete_set,
        values={"BUS", "EXT", "IMM"},
    )

    trigger_voltage = Instrument.control(
        "VOLT:TRIG?", "VOLT:TRIG %d",
        """
        Control voltage to be transferred to output by *TRG command.
        """,
        validator=truncated_range,
        values=[-1*_Vmax, _Vmax]
    )

    trigger_current = Instrument.control(
        "CURR:TRIG?", "CURR:TRIG %d",
        """
        Control current to be transferred to output by *TRG command.
        """,
        validator=truncated_range,
        values=[-1*_Imax, _Imax]
    )

    trigger_continuous = Instrument.control(
        "INIT:CONT?", "INIT:CONT %d",
        """
        Control the state of the continuous trigger.
        
        ====== =======
        Value  Meaning
        ====== =======
        False  arm_single_trigger is necessary to arm the trigger system for a single trigger. 
        True   Trigger system is continuously armed and arm_single_trigger is redundant.
        ====== =======
        """,
        validator=strict_discrete_set,
        values={False: 0, True: 1},
        map_values=True,
    )

    voltage_protect_limit = Instrument.control(
        "VOLT:PROT:LIM?", "VOLT:PROT:LIM %d",
        """
        Control the protection voltage limit of the output. Must be 1.01 times larger than spec.
        """,
        validator=truncated_range,
        values=[-1 * _Vmax * 1.01, _Vmax * 1.01]
    )

    current_protect_limit = Instrument.control(
        "CURR:PROT:LIM?", "CURR:PROT:LIM %d",
        """
        Control the protection current limit of the output. Must be 1.01 times larger than spec.
        """,
        validator=truncated_range,
        values=[-1 * _Imax * 1.01, _Imax * 1.01]
    )

    voltage_limit = Instrument.control(
        "VOLT:LIM?", "VOLT:LIM %d",
        """
        Control the maximum possible voltage programmable at the output.
        """,
        validator=truncated_range,
        values=[-1 * _Vmax, _Vmax]
    )

    current_limit = Instrument.control(
        "CURR:LIM?", "CURR:LIM %d",
        """
        Control the maximum possible current programmable at the output.
        """,
        validator=truncated_range,
        values=[-1 * _Imax, _Imax]
    )

    def arm_single_trigger(self):
        """Function enables the use of single trigger and prepares the PS to receive a single trigger."""
        message = "INIT:IMM; *WAI"
        self.write(message)

    def single_trigger(self):
        """Function sends a single trigger. Needs arm_single_trigger before"""
        message = "*TRG"
        self.write(message)

    def remote_output(self):
        """Function disables physical trigger port and unit output can be controlled remotely"""
        message = "OUTP:CONT OFF"
        self.write(message)

    def establish_limits(self, volt: float, curr: float, store: bool):
        """Function that sets the voltage and current limits, with the possibility of storing them in memory."""
        self.voltage_protect_limit = volt * 1.01
        self.current_protect_limit = curr * 1.01
        self.voltage_limit = volt
        self.current_limit = curr

        if store:
            message = "MEM:UPD LIM"
            self.write(message)

    def save_state(self, slot: int):
        """Functions that saves the current state of the PS to a memory slot.
        Memory slots go from 1-99. 1-15 can be used for power-up setup by using S3 switches (see pg. 2-4)
        """
        message = "*SAV " + str(slot)
        self.write(message)

    def recall_state(self, slot: int):
        """Functions that restores the PS to a state saved in a memory slot.
        Memory slots go from 1-99.
        """
        message = "*RCL " + str(slot) + "; *OPC"
        self.write(message)

