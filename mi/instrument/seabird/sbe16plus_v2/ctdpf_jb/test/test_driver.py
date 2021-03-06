"""
@package mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.test.test_driver
@file marine-integrations/mi/instrument/seabird/sbe16plus_v2/ctdpf_jb/driver.py
@author Tapana Gupta
@brief Test cases for ctdpf_jb driver

USAGE:
 Make tests verbose and provide stdout
   * From the IDK
       $ bin/test_driver
       $ bin/test_driver -u [-t testname]
       $ bin/test_driver -i [-t testname]
       $ bin/test_driver -q [-t testname]
"""

__author__ = 'Tapana Gupta'
__license__ = 'Apache 2.0'

import unittest
import time

from nose.plugins.attrib import attr
from mock import Mock

from mi.core.log import get_logger ; log = get_logger()

# MI imports.
from mi.idk.unit_test import InstrumentDriverTestCase
from mi.idk.unit_test import InstrumentDriverUnitTestCase
from mi.idk.unit_test import InstrumentDriverIntegrationTestCase
from mi.idk.unit_test import InstrumentDriverQualificationTestCase
from mi.idk.unit_test import DriverTestMixin
from mi.idk.unit_test import ParameterTestConfigKey

from mi.instrument.seabird.sbe16plus_v2.test.test_driver import SBEUnitTestCase

from interface.objects import AgentCommand

from mi.core.instrument.logger_client import LoggerClient

from mi.core.exceptions import InstrumentParameterException
from mi.core.exceptions import InstrumentProtocolException

from mi.core.instrument.chunker import StringChunker
from mi.core.instrument.instrument_driver import DriverAsyncEvent
from mi.core.instrument.instrument_driver import DriverConnectionState
from mi.core.instrument.instrument_driver import DriverProtocolState

from mi.instrument.seabird.sbe16plus_v2.driver import ProtocolState
from mi.instrument.seabird.sbe16plus_v2.driver import ProtocolEvent
from mi.instrument.seabird.sbe16plus_v2.driver import Capability
from mi.instrument.seabird.sbe16plus_v2.driver import SBE16Protocol
from mi.instrument.seabird.sbe16plus_v2.driver import Prompt

from mi.instrument.seabird.test.test_driver import SeaBirdUnitTest
from mi.instrument.seabird.test.test_driver import SeaBirdIntegrationTest
from mi.instrument.seabird.test.test_driver import SeaBirdQualificationTest
from mi.instrument.seabird.test.test_driver import SeaBirdPublicationTest

from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import InstrumentDriver
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import DataParticleType
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import ProtocolState
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import ProtocolEvent
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import Capability
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import Parameter
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import Command
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import SBE19DataParticleKey
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import SBE19ConfigurationParticleKey
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import SBE19HardwareParticleKey
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import SBE19StatusParticleKey
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import SBE19CalibrationParticleKey
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import Prompt
from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import NEWLINE

from mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver import SBE19Protocol

###
#   Driver parameters for the tests
###
InstrumentDriverTestCase.initialize(
    driver_module='mi.instrument.seabird.sbe16plus_v2.ctdpf_jb.driver',
    driver_class="InstrumentDriver",

    instrument_agent_resource_id = 'JI22B5',
    instrument_agent_name = 'seabird_sbe16plus_v2_ctdpf_jb',
    instrument_agent_packet_config = DataParticleType(),

    driver_startup_config = {}
)

#################################### RULES ####################################
#                                                                             #
# Common capabilities in the base class                                       #
#                                                                             #
# Instrument specific stuff in the derived class                              #
#                                                                             #
# Generator spits out either stubs or comments describing test this here,     #
# test that there.                                                            #
#                                                                             #
# Qualification tests are driven through the instrument_agent                 #
#                                                                             #
###############################################################################

###
#   Driver constant definitions
###

###############################################################################
#                           DRIVER TEST MIXIN        		                  #
#     Defines a set of constants and assert methods used for data particle    #
#     verification 														      #
#                                                                             #
#  In python mixin classes are classes designed such that they wouldn't be    #
#  able to stand on their own, but are inherited by other classes generally   #
#  using multiple inheritance.                                                #
#                                                                             #
# This class defines a configuration structure for testing and common assert  #
# methods for validating data particles.									  #
###############################################################################
#class DriverTestMixinSub(DriverTestMixin):
#    def assertSampleDataParticle(self, data_particle):
#        '''
#        Verify a particle is a know particle to this driver and verify the particle is
#        correct
#        @param data_particle: Data particle of unkown type produced by the driver
#        '''
#        if (isinstance(data_particle, RawDataParticle)):
#            self.assert_particle_raw(data_particle)
#        else:
#            log.error("Unknown Particle Detected: %s" % data_particle)
#            self.assertFalse(True)
class SeaBird19plusMixin(DriverTestMixin):

    InstrumentDriver = InstrumentDriver

    '''
    Mixin class used for storing data particle constants and common data assertion methods.
    '''

    # Create some short names for the parameter test config
    TYPE      = ParameterTestConfigKey.TYPE
    READONLY  = ParameterTestConfigKey.READONLY
    STARTUP   = ParameterTestConfigKey.STARTUP
    DA        = ParameterTestConfigKey.DIRECT_ACCESS
    VALUE     = ParameterTestConfigKey.VALUE
    REQUIRED  = ParameterTestConfigKey.REQUIRED
    DEFAULT   = ParameterTestConfigKey.DEFAULT
    STATES    = ParameterTestConfigKey.STATES


    ###
    #  Instrument output (driver input) Definitions
    ###
    VALID_SAMPLE = "04570F0A1E910828FC47BC59F199952C64C9" + NEWLINE

    VALID_GETHD_RESPONSE =  "" + \
"<HardwareData DeviceType = 'SBE19plus' SerialNumber = '01906914'>" + NEWLINE + \
"   <Manufacturer>Sea-Bird Electronics, Inc.</Manufacturer>" + NEWLINE + \
"   <FirmwareVersion>2.3</FirmwareVersion>" + NEWLINE + \
"   <FirmwareDate>16 March 2011 08:50</FirmwareDate>" + NEWLINE + \
"   <CommandSetVersion>1.2</CommandSetVersion>" + NEWLINE + \
"   <PCBAssembly PCBSerialNum = '49577' AssemblyNum = '41054H'/>" + NEWLINE + \
"   <PCBAssembly PCBSerialNum = '46750' AssemblyNum = '41580B'/>" + NEWLINE + \
"   <PCBAssembly PCBSerialNum = '49374' AssemblyNum = '41606'/>" + NEWLINE + \
"   <PCBAssembly PCBSerialNum = '38071' AssemblyNum = '41057A'/>" + NEWLINE + \
"   <MfgDate>29 SEP 2011</MfgDate>" + NEWLINE + \
"   <InternalSensors>" + NEWLINE + \
"      <Sensor id = 'Main Temperature'>" + NEWLINE + \
"         <type>temperature0</type>" + NEWLINE + \
"         <SerialNumber>01906914</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"      <Sensor id = 'Main Conductivity'>" + NEWLINE + \
"         <type>conductivity-0</type>" + NEWLINE + \
"         <SerialNumber>01906914</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"      <Sensor id = 'Main Pressure'>" + NEWLINE + \
"         <type>strain-0</type>" + NEWLINE + \
"         <SerialNumber>3313899</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"   </InternalSensors>" + NEWLINE + \
"   <ExternalSensors>" + NEWLINE + \
"      <Sensor id = 'volt 0'>" + NEWLINE + \
"         <type>not assigned</type>" + NEWLINE + \
"         <SerialNumber>not assigned</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"      <Sensor id = 'volt 1'>" + NEWLINE + \
"         <type>not assigned</type>" + NEWLINE + \
"         <SerialNumber>not assigned</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"      <Sensor id = 'volt 2'>" + NEWLINE + \
"         <type>not assigned</type>" + NEWLINE + \
"         <SerialNumber>not assigned</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"      <Sensor id = 'volt 3'>" + NEWLINE + \
"         <type>not assigned</type>" + NEWLINE + \
"         <SerialNumber>not assigned</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"      <Sensor id = 'volt 4'>" + NEWLINE + \
"         <type>not assigned</type>" + NEWLINE + \
"         <SerialNumber>not assigned</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"      <Sensor id = 'volt 5'>" + NEWLINE + \
"         <type>not assigned</type>" + NEWLINE + \
"         <SerialNumber>not assigned</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"      <Sensor id = 'serial'>" + NEWLINE + \
"         <type>not assigned</type>" + NEWLINE + \
"         <SerialNumber>not assigned</SerialNumber>" + NEWLINE + \
"      </Sensor>" + NEWLINE + \
"   </ExternalSensors>" + NEWLINE + \
"</HardwareData>" + NEWLINE


    VALID_GETCC_RESPONSE =  "" + \
"<CalibrationCoefficients DeviceType = 'SBE19plus' SerialNumber = '01906914'>" + NEWLINE + \
"   <Calibration format = 'TEMP1' id = 'Main Temperature'>" + NEWLINE + \
"      <SerialNum>01906914</SerialNum>" + NEWLINE + \
"      <CalDate>09-Oct-11</CalDate>" + NEWLINE + \
"      <TA0>1.254755e-03</TA0>" + NEWLINE + \
"      <TA1>2.758871e-04</TA1>" + NEWLINE + \
"      <TA2>-1.368268e-06</TA2>" + NEWLINE + \
"      <TA3>1.910795e-07</TA3>" + NEWLINE + \
"      <TOFFSET>0.000000e+00</TOFFSET>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'WBCOND0' id = 'Main Conductivity'>" + NEWLINE + \
"      <SerialNum>01906914</SerialNum>" + NEWLINE + \
"      <CalDate>09-Oct-11</CalDate>" + NEWLINE + \
"      <G>-9.761799e-01</G>" + NEWLINE + \
"      <H>1.369994e-01</H>" + NEWLINE + \
"      <I>-3.523860e-04</I>" + NEWLINE + \
"      <J>4.404252e-05</J>" + NEWLINE + \
"      <CPCOR>-9.570000e-08</CPCOR>" + NEWLINE + \
"      <CTCOR>3.250000e-06</CTCOR>" + NEWLINE + \
"      <CSLOPE>1.000000e+00</CSLOPE>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'STRAIN0' id = 'Main Pressure'>" + NEWLINE + \
"      <SerialNum>3313899</SerialNum>" + NEWLINE + \
"      <CalDate>06-Oct-11</CalDate>" + NEWLINE + \
"      <PA0>-3.689246e-02</PA0>" + NEWLINE + \
"      <PA1>1.545570e-03</PA1>" + NEWLINE + \
"      <PA2>6.733197e-12</PA2>" + NEWLINE + \
"      <PTCA0>5.249034e+05</PTCA0>" + NEWLINE + \
"      <PTCA1>1.423189e+00</PTCA1>" + NEWLINE + \
"      <PTCA2>-1.206562e-01</PTCA2>" + NEWLINE + \
"      <PTCB0>2.501288e+01</PTCB0>" + NEWLINE + \
"      <PTCB1>-2.250000e-04</PTCB1>" + NEWLINE + \
"      <PTCB2>0.000000e+00</PTCB2>" + NEWLINE + \
"      <PTEMPA0>-5.677620e+01</PTEMPA0>" + NEWLINE + \
"      <PTEMPA1>5.424624e+01</PTEMPA1>" + NEWLINE + \
"      <PTEMPA2>-2.278113e-01</PTEMPA2>" + NEWLINE + \
"      <POFFSET>0.000000e+00</POFFSET>" + NEWLINE + \
"      <PRANGE>5.080000e+02</PRANGE>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'VOLT0' id = 'Volt 0'>" + NEWLINE + \
"      <OFFSET>-4.650526e-02</OFFSET>" + NEWLINE + \
"      <SLOPE>1.246381e+00</SLOPE>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'VOLT0' id = 'Volt 1'>" + NEWLINE + \
"      <OFFSET>-4.618105e-02</OFFSET>" + NEWLINE + \
"      <SLOPE>1.247197e+00</SLOPE>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'VOLT0' id = 'Volt 2'>" + NEWLINE + \
"      <OFFSET>-4.659790e-02</OFFSET>" + NEWLINE + \
"      <SLOPE>1.247601e+00</SLOPE>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'VOLT0' id = 'Volt 3'>" + NEWLINE + \
"      <OFFSET>-4.502421e-02</OFFSET>" + NEWLINE + \
"      <SLOPE>1.246911e+00</SLOPE>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'VOLT0' id = 'Volt 4'>" + NEWLINE + \
"      <OFFSET>-4.589158e-02</OFFSET>" + NEWLINE + \
"      <SLOPE>1.246346e+00</SLOPE>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'VOLT0' id = 'Volt 5'>" + NEWLINE + \
"      <OFFSET>-4.609895e-02</OFFSET>" + NEWLINE + \
"      <SLOPE>1.247868e+00</SLOPE>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"   <Calibration format = 'FREQ0' id = 'external frequency channel'>" + NEWLINE + \
"      <EXTFREQSF>1.000008e+00</EXTFREQSF>" + NEWLINE + \
"   </Calibration>" + NEWLINE + \
"</CalibrationCoefficients>" + NEWLINE


    VALID_GETCD_RESPONSE =  "" + \
"<ConfigurationData DeviceType = 'SBE19plus' SerialNumber = '01906914'>" + NEWLINE + \
"   <ProfileMode>" + NEWLINE + \
"      <ScansToAverage>4</ScansToAverage>" + NEWLINE + \
"      <MinimumCondFreq>2500</MinimumCondFreq>" + NEWLINE + \
"      <PumpDelay>15</PumpDelay>" + NEWLINE + \
"      <AutoRun>no</AutoRun>" + NEWLINE + \
"      <IgnoreSwitch>yes</IgnoreSwitch>" + NEWLINE + \
"   </ProfileMode>" + NEWLINE + \
"   <Battery>" + NEWLINE + \
"      <Type>alkaline</Type>" + NEWLINE + \
"      <CutOff>7.5</CutOff>" + NEWLINE + \
"   </Battery>" + NEWLINE + \
"   <DataChannels>" + NEWLINE + \
"      <ExtVolt0>yes</ExtVolt0>" + NEWLINE + \
"      <ExtVolt1>yes</ExtVolt1>" + NEWLINE + \
"      <ExtVolt2>no</ExtVolt2>" + NEWLINE + \
"      <ExtVolt3>no</ExtVolt3>" + NEWLINE + \
"      <ExtVolt4>no</ExtVolt4>" + NEWLINE + \
"      <ExtVolt5>no</ExtVolt5>" + NEWLINE + \
"      <SBE38>no</SBE38>" + NEWLINE + \
"      <WETLABS>no</WETLABS>" + NEWLINE + \
"      <OPTODE>yes</OPTODE>" + NEWLINE + \
"      <GTD>no</GTD>" + NEWLINE + \
"   </DataChannels>" + NEWLINE + \
"   <EchoCharacters>yes</EchoCharacters>" + NEWLINE + \
"   <OutputExecutedTag>no</OutputExecutedTag>" + NEWLINE + \
"   <OutputFormat>raw HEX</OutputFormat>" + NEWLINE + \
"</ConfigurationData>" + NEWLINE


    VALID_GETSD_RESPONSE =  "" + \
"<StatusData DeviceType = 'SBE19plus' SerialNumber = '01906914'>" + NEWLINE + \
"   <DateTime>2014-03-20T09:09:06</DateTime>" + NEWLINE + \
"   <LoggingState>not logging</LoggingState>" + NEWLINE + \
"   <EventSummary numEvents = '260'/>" + NEWLINE + \
"   <Power>" + NEWLINE + \
"      <vMain>13.0</vMain>" + NEWLINE + \
"      <vLith>8.6</vLith>" + NEWLINE + \
"      <iMain>51.1</iMain>" + NEWLINE + \
"      <iPump>145.6</iPump>" + NEWLINE + \
"      <iExt01> 0.5</iExt01>" + NEWLINE + \
"      <iSerial>45.1</iSerial>" + NEWLINE + \
"   </Power>" + NEWLINE + \
"   <MemorySummary>" + NEWLINE + \
"      <Bytes>330</Bytes>" + NEWLINE + \
"      <Samples>15</Samples>" + NEWLINE + \
"      <SamplesFree>2990809</SamplesFree>" + NEWLINE + \
"      <SampleLength>18</SampleLength>" + NEWLINE + \
"      <Profiles>0</Profiles>" + NEWLINE + \
"   </MemorySummary>" + NEWLINE + \
"</StatusData>" + NEWLINE


    ###
    #  Parameter and Type Definitions
    ###

    _sample_parameters = {
        SBE19DataParticleKey.TEMP: {TYPE: int, VALUE: 284431, REQUIRED: True },
        SBE19DataParticleKey.CONDUCTIVITY: {TYPE: int, VALUE: 663185, REQUIRED: True },
        SBE19DataParticleKey.PRESSURE: {TYPE: int, VALUE: 534780, REQUIRED: True },
        SBE19DataParticleKey.PRESSURE_TEMP: {TYPE: int, VALUE: 18364, REQUIRED: True },
        SBE19DataParticleKey.VOLT0: {TYPE: int, VALUE: 23025, REQUIRED: True },
        SBE19DataParticleKey.VOLT1: {TYPE: int, VALUE: 39317, REQUIRED: True },
        SBE19DataParticleKey.OXYGEN: {TYPE: int, VALUE: 2909385, REQUIRED: True },

    }

    _configuration_parameters = {
        SBE19ConfigurationParticleKey.SERIAL_NUMBER: {TYPE: int, VALUE: 1906914, REQUIRED: True},
        SBE19ConfigurationParticleKey.SCANS_TO_AVERAGE: {TYPE: int, VALUE: 4, REQUIRED: True},
        SBE19ConfigurationParticleKey.MIN_COND_FREQ: {TYPE: int, VALUE: 2500, REQUIRED: True},
        SBE19ConfigurationParticleKey.PUMP_DELAY: {TYPE: int, VALUE: 15, REQUIRED: True},
        SBE19ConfigurationParticleKey.AUTO_RUN: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.IGNORE_SWITCH: {TYPE: bool, VALUE: True, REQUIRED: True},
        SBE19ConfigurationParticleKey.BATTERY_TYPE: {TYPE: unicode, VALUE: "alkaline", REQUIRED: True},
        SBE19ConfigurationParticleKey.BATTERY_CUTOFF: {TYPE: float, VALUE: 7.5, REQUIRED: True},
        SBE19ConfigurationParticleKey.EXT_VOLT_0: {TYPE: bool, VALUE: True, REQUIRED: True},
        SBE19ConfigurationParticleKey.EXT_VOLT_1: {TYPE: bool, VALUE: True, REQUIRED: True},
        SBE19ConfigurationParticleKey.EXT_VOLT_2: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.EXT_VOLT_3: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.EXT_VOLT_4: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.EXT_VOLT_5: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.SBE38: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.WETLABS: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.OPTODE: {TYPE: bool, VALUE: True, REQUIRED: True},
        SBE19ConfigurationParticleKey.GAS_TENSION_DEVICE: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.ECHO_CHARACTERS: {TYPE: bool, VALUE: True, REQUIRED: True},
        SBE19ConfigurationParticleKey.OUTPUT_EXECUTED_TAG: {TYPE: bool, VALUE: False, REQUIRED: True},
        SBE19ConfigurationParticleKey.OUTPUT_FORMAT: {TYPE: unicode, VALUE: "raw HEX", REQUIRED: True},
    }
    
    _status_parameters = {
        SBE19StatusParticleKey.SERIAL_NUMBER: {TYPE: int, VALUE: 1906914, REQUIRED: True},
        SBE19StatusParticleKey.DATE_TIME: {TYPE: unicode, VALUE: "2014-03-20T09:09:06", REQUIRED: True},
        SBE19StatusParticleKey.LOGGING_STATE: {TYPE: unicode, VALUE: "not logging", REQUIRED: True},
        SBE19StatusParticleKey.NUMBER_OF_EVENTS: {TYPE: int, VALUE: 260, REQUIRED: True},
        SBE19StatusParticleKey.BATTERY_VOLTAGE_MAIN: {TYPE: float, VALUE: 13.0, REQUIRED: True},
        SBE19StatusParticleKey.BATTERY_VOLTAGE_LITHIUM: {TYPE: float, VALUE: 8.6, REQUIRED: True},
        SBE19StatusParticleKey.OPERATIONAL_CURRENT: {TYPE: float, VALUE: 51.1, REQUIRED: True},
        SBE19StatusParticleKey.PUMP_CURRENT: {TYPE: float, VALUE: 145.6, REQUIRED: True},
        SBE19StatusParticleKey.EXT_V01_CURRENT: {TYPE: float, VALUE: 0.5, REQUIRED: True},
        SBE19StatusParticleKey.SERIAL_CURRENT: {TYPE: float, VALUE: 45.1, REQUIRED: True},
        SBE19StatusParticleKey.MEMORY_FREE: {TYPE: int, VALUE: 330, REQUIRED: True},
        SBE19StatusParticleKey.NUMBER_OF_SAMPLES: {TYPE: int, VALUE: 15, REQUIRED: True},
        SBE19StatusParticleKey.SAMPLES_FREE: {TYPE: int, VALUE: 2990809, REQUIRED: True},
        SBE19StatusParticleKey.SAMPLE_LENGTH: {TYPE: int, VALUE: 18, REQUIRED: True},
        SBE19StatusParticleKey.PROFILES: {TYPE: int, VALUE: 0, REQUIRED: True},
    }

    _hardware_parameters = {
        SBE19HardwareParticleKey.SERIAL_NUMBER: {TYPE: int, VALUE: 1906914, REQUIRED: True},
        SBE19HardwareParticleKey.MANUFACTURER: {TYPE: unicode, VALUE: "Sea-Bird Electronics, Inc.", REQUIRED: True},
        SBE19HardwareParticleKey.FIRMWARE_VERSION: {TYPE: unicode, VALUE: '2.3', REQUIRED: True},
        SBE19HardwareParticleKey.FIRMWARE_DATE: {TYPE: unicode, VALUE: '16 March 2011 08:50', REQUIRED: True},
        SBE19HardwareParticleKey.COMMAND_SET_VERSION: {TYPE: unicode, VALUE: '1.2', REQUIRED: True},
        SBE19HardwareParticleKey.PCB_SERIAL_NUMBER: {TYPE: list, VALUE: ['49577', '46750', '49374', '38071'], REQUIRED: True},
        SBE19HardwareParticleKey.ASSEMBLY_NUMBER: {TYPE: list, VALUE: ['41054H', '41580B', '41606', '41057A'], REQUIRED: True},
        SBE19HardwareParticleKey.MANUFACTURE_DATE: {TYPE: unicode, VALUE: '29 SEP 2011', REQUIRED: True},
        SBE19HardwareParticleKey.TEMPERATURE_SENSOR_SERIAL_NUMBER: {TYPE: int, VALUE: 1906914, REQUIRED: True},
        SBE19HardwareParticleKey.TEMPERATURE_SENSOR_TYPE: {TYPE: unicode, VALUE: 'temperature0', REQUIRED: True},
        SBE19HardwareParticleKey.CONDUCTIVITY_SENSOR_SERIAL_NUMBER: {TYPE: int, VALUE: 1906914, REQUIRED: True},
        SBE19HardwareParticleKey.CONDUCTIVITY_SENSOR_TYPE: {TYPE: unicode, VALUE: 'conductivity-0', REQUIRED: True},
        SBE19HardwareParticleKey.PRESSURE_SENSOR_SERIAL_NUMBER: {TYPE: int, VALUE: 3313899, REQUIRED: True},
        SBE19HardwareParticleKey.PRESSURE_SENSOR_TYPE: {TYPE: unicode, VALUE: 'strain-0', REQUIRED: True},
    }
    
    _calibration_parameters = {
        SBE19CalibrationParticleKey.SERIAL_NUMBER: {TYPE: int, VALUE: 1906914, REQUIRED: True},
        SBE19CalibrationParticleKey.TEMP_SENSOR_SERIAL_NUMBER: {TYPE: int, VALUE: 1906914, REQUIRED: True },
        SBE19CalibrationParticleKey.TEMP_CAL_DATE: {TYPE: unicode, VALUE: "09-Oct-11", REQUIRED: True},
        SBE19CalibrationParticleKey.TA0: {TYPE: float, VALUE: 1.254755e-03, REQUIRED: True},
        SBE19CalibrationParticleKey.TA1: {TYPE: float, VALUE: 2.758871e-04, REQUIRED: True},
        SBE19CalibrationParticleKey.TA2: {TYPE: float, VALUE: -1.368268e-06, REQUIRED: True},
        SBE19CalibrationParticleKey.TA3: {TYPE: float, VALUE: 1.910795e-07, REQUIRED: True},
        SBE19CalibrationParticleKey.TOFFSET: {TYPE: float, VALUE: 0.0, REQUIRED: True},
        SBE19CalibrationParticleKey.COND_SENSOR_SERIAL_NUMBER: {TYPE: int, VALUE: 1906914, REQUIRED: True },
        SBE19CalibrationParticleKey.COND_CAL_DATE: {TYPE: unicode, VALUE: '09-Oct-11', REQUIRED: True},
        SBE19CalibrationParticleKey.CONDG: {TYPE: float, VALUE: -9.761799e-01, REQUIRED: True},
        SBE19CalibrationParticleKey.CONDH: {TYPE: float, VALUE: 1.369994e-01, REQUIRED: True},
        SBE19CalibrationParticleKey.CONDI: {TYPE: float, VALUE: -3.523860e-04, REQUIRED: True},
        SBE19CalibrationParticleKey.CONDJ: {TYPE: float, VALUE: 4.404252e-05, REQUIRED: True},
        SBE19CalibrationParticleKey.CPCOR: {TYPE: float, VALUE: -9.570000e-08, REQUIRED: True},
        SBE19CalibrationParticleKey.CTCOR: {TYPE: float, VALUE: 3.250000e-06, REQUIRED: True},
        SBE19CalibrationParticleKey.CSLOPE: {TYPE: float, VALUE: 1.0, REQUIRED: True},
        SBE19CalibrationParticleKey.PRES_SERIAL_NUMBER: {TYPE: int, VALUE: 3313899, REQUIRED: True },
        SBE19CalibrationParticleKey.PRES_CAL_DATE: {TYPE: unicode, VALUE: '06-Oct-11', REQUIRED: True },
        SBE19CalibrationParticleKey.PA0: {TYPE: float, VALUE: -3.689246e-02, REQUIRED: True },
        SBE19CalibrationParticleKey.PA1: {TYPE: float, VALUE: 1.545570e-03, REQUIRED: True },
        SBE19CalibrationParticleKey.PA2: {TYPE: float, VALUE: 6.733197e-12, REQUIRED: True },
        SBE19CalibrationParticleKey.PTCA0: {TYPE: float, VALUE: 5.249034e+05, REQUIRED: True },
        SBE19CalibrationParticleKey.PTCA1: {TYPE: float, VALUE: 1.423189e+00, REQUIRED: True },
        SBE19CalibrationParticleKey.PTCA2: {TYPE: float, VALUE: -1.206562e-01, REQUIRED: True },
        SBE19CalibrationParticleKey.PTCB0: {TYPE: float, VALUE: 2.501288e+01, REQUIRED: True },
        SBE19CalibrationParticleKey.PTCB1: {TYPE: float, VALUE: -2.250000e-04, REQUIRED: True },
        SBE19CalibrationParticleKey.PTCB2: {TYPE: float, VALUE: 0.000000e+00, REQUIRED: True },
        SBE19CalibrationParticleKey.PTEMPA0: {TYPE: float, VALUE: -5.677620e+01, REQUIRED: True },
        SBE19CalibrationParticleKey.PTEMPA1: {TYPE: float, VALUE: 5.424624e+01, REQUIRED: True },
        SBE19CalibrationParticleKey.PTEMPA2: {TYPE: float, VALUE: -2.278113e-01, REQUIRED: True },
        SBE19CalibrationParticleKey.POFFSET: {TYPE: float, VALUE: 0.000000e+00, REQUIRED: True },
        SBE19CalibrationParticleKey.PRES_RANGE: {TYPE: int, VALUE: 508, REQUIRED: True },
        SBE19CalibrationParticleKey.EXT_VOLT0_OFFSET: {TYPE: float, VALUE: -4.650526e-02, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT0_SLOPE: {TYPE: float, VALUE: 1.246381e+00, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT1_OFFSET: {TYPE: float, VALUE: -4.618105e-02, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT1_SLOPE: {TYPE: float, VALUE: 1.247197e+00, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT2_OFFSET: {TYPE: float, VALUE: -4.659790e-02, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT2_SLOPE: {TYPE: float, VALUE: 1.247601e+00, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT3_OFFSET: {TYPE: float, VALUE: -4.502421e-02, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT3_SLOPE: {TYPE: float, VALUE: 1.246911e+00, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT4_OFFSET: {TYPE: float, VALUE: -4.589158e-02, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT4_SLOPE: {TYPE: float, VALUE: 1.246346e+00, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT5_OFFSET: {TYPE: float, VALUE: -4.609895e-02, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_VOLT5_SLOPE: {TYPE: float, VALUE: 1.247868e+00, REQUIRED: True},
        SBE19CalibrationParticleKey.EXT_FREQ: {TYPE: float, VALUE: 1.000008e+00, REQUIRED: True},
    }

    #TODO: incomplete - needs to be verified and matched with driver/IOS
    ###
    #  Parameter and Type Definitions
    ###
    _driver_parameters = {
        # Parameters defined in the IOS
        Parameter.DATE_TIME : {TYPE: str, READONLY: True, DA: False, STARTUP: False},
        Parameter.ECHO : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.OUTPUT_EXEC_TAG : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.PTYPE : {TYPE: int, READONLY: True, DA: True, STARTUP: True, DEFAULT: 1, VALUE: 1},
        Parameter.VOLT0 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.VOLT1 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.VOLT2 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.VOLT3 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.VOLT4 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.VOLT5 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: True, VALUE: True},
        Parameter.SBE38 : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.WETLABS : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.GTD : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.OPTODE : {TYPE: bool, READONLY: True, DA: True, STARTUP: True, DEFAULT: False, VALUE: False},
        Parameter.OUTPUT_FORMAT : {TYPE: int, READONLY: True, DA: True, STARTUP: True, DEFAULT: 0, VALUE: 0},
        Parameter.LOGGING : {TYPE: bool, READONLY: True, DA: False, STARTUP: False},
    }

    #TODO: needs to be verified and matched with driver/IOS
    _driver_capabilities = {
        # capabilities defined in the IOS
        Capability.QUIT_SESSION : {STATES: [ProtocolState.COMMAND, ProtocolState.AUTOSAMPLE]},
        Capability.START_AUTOSAMPLE : {STATES: [ProtocolState.COMMAND]},
        Capability.STOP_AUTOSAMPLE : {STATES: [ProtocolState.AUTOSAMPLE]},
        Capability.CLOCK_SYNC : {STATES: [ProtocolState.COMMAND]},
        Capability.ACQUIRE_STATUS : {STATES: [ProtocolState.COMMAND, ProtocolState.AUTOSAMPLE]},
        Capability.GET_CONFIGURATION : {STATES: [ProtocolState.COMMAND, ProtocolState.AUTOSAMPLE]},
        Capability.TEST : {STATES: [ProtocolState.COMMAND]},
        Capability.RESET_EC : {STATES: [ProtocolState.COMMAND]},

    }


    def assert_particle_sample(self, data_particle, verify_values = False):
        '''
        Verify sample particle
        @param data_particle:  SBE19DataParticle data particle
        @param verify_values:  bool, should we verify parameter values
        '''
        self.assert_data_particle_keys(SBE19DataParticleKey, self._sample_parameters)
        self.assert_data_particle_header(data_particle, DataParticleType.CTD_PARSED, require_instrument_timestamp=False)
        self.assert_data_particle_parameters(data_particle, self._sample_parameters, verify_values)

    def assert_particle_hardware(self, data_particle, verify_values = False):
        '''
        Verify hardware particle
        @param data_particle:  SBE19HardwareParticle data particle
        @param verify_values:  bool, should we verify parameter values
        '''
        self.assert_data_particle_keys(SBE19HardwareParticleKey, self._hardware_parameters)
        self.assert_data_particle_header(data_particle, DataParticleType.DEVICE_HARDWARE)
        self.assert_data_particle_parameters(data_particle, self._hardware_parameters, verify_values)

    def assert_particle_calibration(self, data_particle, verify_values = False):
        '''
        Verify sample particle
        @param data_particle:  SBE19CalibrationParticle calibration particle
        @param verify_values:  bool, should we verify parameter values
        '''
        self.assert_data_particle_keys(SBE19CalibrationParticleKey, self._calibration_parameters)
        self.assert_data_particle_header(data_particle, DataParticleType.DEVICE_CALIBRATION)
        self.assert_data_particle_parameters(data_particle, self._calibration_parameters, verify_values)

    def assert_particle_status(self, data_particle, verify_values = False):
        '''
        Verify status particle
        @param data_particle:  SBE19StatusParticle status particle
        @param verify_values:  bool, should we verify parameter values
        '''
        self.assert_data_particle_keys(SBE19StatusParticleKey, self._status_parameters)
        self.assert_data_particle_header(data_particle, DataParticleType.DEVICE_STATUS)
        self.assert_data_particle_parameters(data_particle, self._status_parameters, verify_values)

    def assert_particle_configuration(self, data_particle, verify_values = False):
        '''
        Verify configuration particle
        @param data_particle:  SBE19ConfigurationParticle configuration particle
        @param verify_values:  bool, should we verify parameter values
        '''
        self.assert_data_particle_keys(SBE19ConfigurationParticleKey, self._configuration_parameters)
        self.assert_data_particle_header(data_particle, DataParticleType.DEVICE_CONFIGURATION)
        self.assert_data_particle_parameters(data_particle, self._configuration_parameters, verify_values)



###############################################################################
#                                UNIT TESTS                                   #
#         Unit tests test the method calls and parameters using Mock.         #
#                                                                             #
#   These tests are especially useful for testing parsers and other data      #
#   handling.  The tests generally focus on small segments of code, like a    #
#   single function call, but more complex code using Mock objects.  However  #
#   if you find yourself mocking too much maybe it is better as an            #
#   integration test.                                                         #
#                                                                             #
#   Unit tests do not start up external processes like the port agent or      #
#   driver process.                                                           #
###############################################################################
@attr('UNIT', group='mi')
class SBE19UnitTestCase(SeaBirdUnitTest, SeaBird19plusMixin):


    def test_driver_enums(self):
        """
        Verify that all driver enumeration has no duplicate values that might cause confusion.  Also
        do a little extra validation for the Capabilites
        """
        self.assert_enum_has_no_duplicates(Command())
        self.assert_enum_has_no_duplicates(DataParticleType())
        self.assert_enum_has_no_duplicates(ProtocolState())
        self.assert_enum_has_no_duplicates(ProtocolEvent())
        self.assert_enum_has_no_duplicates(Parameter())

        # Test capabilites for duplicates, then verify that capabilities is a subset of proto events
        self.assert_enum_has_no_duplicates(Capability())
        self.assert_enum_complete(Capability(), ProtocolEvent())

    #TODO: once IOS is stable, remove annotation below
    @unittest.skip("re-visit once IOS is stable")
    def test_driver_schema(self):
        """
        get the driver schema and verify it is configured properly
        """
        driver = self.InstrumentDriver(self._got_data_event_callback)
        self.assert_driver_schema(driver, self._driver_parameters, self._driver_capabilities)


    def test_chunker(self):
        """
        Test the chunker and verify the particles created.
        """
        chunker = StringChunker(SBE19Protocol.sieve_function)

        self.assert_chunker_sample(chunker, self.VALID_SAMPLE)
        self.assert_chunker_sample_with_noise(chunker, self.VALID_SAMPLE)
        self.assert_chunker_fragmented_sample(chunker, self.VALID_SAMPLE)
        self.assert_chunker_combined_sample(chunker, self.VALID_SAMPLE)

        self.assert_chunker_sample(chunker, self.VALID_GETHD_RESPONSE)
        self.assert_chunker_sample_with_noise(chunker, self.VALID_GETHD_RESPONSE)
        self.assert_chunker_fragmented_sample(chunker, self.VALID_GETHD_RESPONSE)
        self.assert_chunker_combined_sample(chunker, self.VALID_GETHD_RESPONSE)

        self.assert_chunker_sample(chunker, self.VALID_GETCC_RESPONSE)
        self.assert_chunker_sample_with_noise(chunker, self.VALID_GETCC_RESPONSE)
        self.assert_chunker_fragmented_sample(chunker, self.VALID_GETCC_RESPONSE)
        self.assert_chunker_combined_sample(chunker, self.VALID_GETCC_RESPONSE)

        self.assert_chunker_sample(chunker, self.VALID_GETSD_RESPONSE)
        self.assert_chunker_sample_with_noise(chunker, self.VALID_GETSD_RESPONSE)
        self.assert_chunker_fragmented_sample(chunker, self.VALID_GETSD_RESPONSE)
        self.assert_chunker_combined_sample(chunker, self.VALID_GETSD_RESPONSE)

        self.assert_chunker_sample(chunker, self.VALID_GETCD_RESPONSE)
        self.assert_chunker_sample_with_noise(chunker, self.VALID_GETCD_RESPONSE)
        self.assert_chunker_fragmented_sample(chunker, self.VALID_GETCD_RESPONSE)
        self.assert_chunker_combined_sample(chunker, self.VALID_GETCD_RESPONSE)


    def test_got_data(self):
        """
        Verify sample data passed through the got data method produces the correct data particles
        """
        # Create and initialize the instrument driver with a mock port agent
        driver = InstrumentDriver(self._got_data_event_callback)
        self.assert_initialize_driver(driver)

        self.assert_raw_particle_published(driver, True)

        # Start validating data particles
        self.assert_particle_published(driver, self.VALID_SAMPLE, self.assert_particle_sample, True)
        self.assert_particle_published(driver, self.VALID_GETHD_RESPONSE, self.assert_particle_hardware, True)
        self.assert_particle_published(driver, self.VALID_GETCC_RESPONSE, self.assert_particle_calibration, True)
        self.assert_particle_published(driver, self.VALID_GETSD_RESPONSE, self.assert_particle_status, True)
        self.assert_particle_published(driver, self.VALID_GETCD_RESPONSE, self.assert_particle_configuration, True)


    def test_capabilities(self):
        """
        Verify the FSM reports capabilities as expected.  All states defined in this dict must
        also be defined in the protocol FSM.
        """
        capabilities = {
            ProtocolState.UNKNOWN: ['DRIVER_EVENT_DISCOVER'],
            ProtocolState.TEST: ['DRIVER_EVENT_GET',
                                 'DRIVER_EVENT_RUN_TEST'],
            ProtocolState.COMMAND: ['DRIVER_EVENT_ACQUIRE_SAMPLE',
                                    'DRIVER_EVENT_ACQUIRE_STATUS',
                                    'DRIVER_EVENT_CLOCK_SYNC',
                                    'DRIVER_EVENT_GET',
                                    'DRIVER_EVENT_SET',
                                    'DRIVER_EVENT_TEST',
                                    'DRIVER_EVENT_START_AUTOSAMPLE',
                                    'DRIVER_EVENT_START_DIRECT',
                                    'PROTOCOL_EVENT_GET_CONFIGURATION',
                                    'PROTOCOL_EVENT_RESET_EC',
                                    'DRIVER_EVENT_SCHEDULED_CLOCK_SYNC'],
            ProtocolState.AUTOSAMPLE: ['DRIVER_EVENT_GET',
                                       'PROTOCOL_EVENT_QUIT_SESSION',
                                       'DRIVER_EVENT_STOP_AUTOSAMPLE',
                                       'PROTOCOL_EVENT_GET_CONFIGURATION',
                                       'DRIVER_EVENT_SCHEDULED_CLOCK_SYNC',
                                       'DRIVER_EVENT_ACQUIRE_STATUS'],
            ProtocolState.DIRECT_ACCESS: ['DRIVER_EVENT_STOP_DIRECT', 'EXECUTE_DIRECT']
        }

        driver = InstrumentDriver(self._got_data_event_callback)
        self.assert_capabilities(driver, capabilities)

    #TODO
    def test_parse_ds(self):
        pass

    def test_parse_set_response(self):
        """
        Test response from set commands.
        """
        driver = self.InstrumentDriver(self._got_data_event_callback)
        self.assert_initialize_driver(driver, ProtocolState.COMMAND)

        response = "Not an error"
        driver._protocol._parse_set_response(response, Prompt.EXECUTED)
        driver._protocol._parse_set_response(response, Prompt.COMMAND)

        with self.assertRaises(InstrumentProtocolException):
            driver._protocol._parse_set_response(response, Prompt.BAD_COMMAND)

        response = "<ERROR type='INVALID ARGUMENT' msg='out of range'/>"
        with self.assertRaises(InstrumentParameterException):
            driver._protocol._parse_set_response(response, Prompt.EXECUTED)


###############################################################################
#                            INTEGRATION TESTS                                #
#     Integration test test the direct driver / instrument interaction        #
#     but making direct calls via zeromq.                                     #
#     - Common Integration tests test the driver through the instrument agent #
#     and common for all drivers (minimum requirement for ION ingestion)      #
###############################################################################
@attr('INT', group='mi')
class SBE19IntegrationTest(SeaBirdIntegrationTest, SeaBird19plusMixin):
    def test_connection(self):
        self.assert_initialize_driver()

    def test_polled(self):
        """
        Test that we can generate particles with commands while in command mode
        """
        self.assert_initialize_driver()

        # test acquire_sample data particle
        self.assert_particle_generation(ProtocolEvent.ACQUIRE_SAMPLE, DataParticleType.CTD_PARSED, self.assert_particle_sample)

    def test_status(self):
        self.assert_initialize_driver()

        # test acquire_status particles
        self.assert_particle_generation(ProtocolEvent.ACQUIRE_STATUS, DataParticleType.DEVICE_STATUS, self.assert_particle_status)
        self.assert_particle_generation(ProtocolEvent.ACQUIRE_STATUS, DataParticleType.DEVICE_HARDWARE, self.assert_particle_hardware)
        #TODO: this one fails
        #self.assert_particle_generation(ProtocolEvent.ACQUIRE_STATUS, DataParticleType.DEVICE_CONFIGURATION, self.assert_particle_configuration)
        self.assert_particle_generation(ProtocolEvent.ACQUIRE_STATUS, DataParticleType.DEVICE_CALIBRATION, self.assert_particle_calibration)

    def test_configuration(self):
        self.assert_initialize_driver()

        # test get_configuration particle
        self.assert_particle_generation(ProtocolEvent.GET_CONFIGURATION, DataParticleType.DEVICE_CALIBRATION, self.assert_particle_calibration)

    def test_autosample(self):
        """
        Verify that we can enter streaming and that all particles are produced
        properly.

        Because we have to test for many different data particles we can't use
        the common assert_sample_autosample method
        """
        self.assert_initialize_driver()
        #TODO: do we need to check value of NAvg here? If so, what should it be set to?
        #self.assert_set(Parameter.INTERVAL, 10)

        self.assert_driver_command(ProtocolEvent.START_AUTOSAMPLE, state=ProtocolState.AUTOSAMPLE, delay=1)
        self.assert_async_particle_generation(DataParticleType.CTD_PARSED, self.assert_particle_sample, timeout=60)

        self.assert_particle_generation(ProtocolEvent.ACQUIRE_STATUS, DataParticleType.DEVICE_STATUS, self.assert_particle_status)
        self.assert_particle_generation(ProtocolEvent.ACQUIRE_STATUS, DataParticleType.DEVICE_HARDWARE, self.assert_particle_hardware)

        #TODO: this one fails
        #self.assert_particle_generation(ProtocolEvent.ACQUIRE_STATUS, DataParticleType.DEVICE_CONFIGURATION, self.assert_particle_configuration)
        self.assert_particle_generation(ProtocolEvent.ACQUIRE_STATUS, DataParticleType.DEVICE_CALIBRATION, self.assert_particle_calibration)

        self.assert_particle_generation(ProtocolEvent.GET_CONFIGURATION, DataParticleType.DEVICE_CALIBRATION, self.assert_particle_calibration)

        self.assert_driver_command(ProtocolEvent.STOP_AUTOSAMPLE, state=ProtocolState.COMMAND, delay=1)

    def test_test(self):
        """
        Test the hardware testing mode.
        """
        self.assert_initialize_driver()

        start_time = time.time()
        timeout = time.time() + 300
        reply = self.driver_client.cmd_dvr('execute_resource', ProtocolEvent.TEST)

        self.assert_current_state(ProtocolState.TEST)

        # Test the driver is in test state.
        state = self.driver_client.cmd_dvr('get_resource_state')

        while state != ProtocolState.COMMAND:
            time.sleep(5)
            elapsed = time.time() - start_time
            log.info('Device testing %f seconds elapsed.' % elapsed)
            state = self.driver_client.cmd_dvr('get_resource_state')
            self.assertLess(time.time(), timeout, msg="Timeout waiting for instrument to come out of test")

        # Verify we received the test result and it passed.
        test_results = [evt for evt in self.events if evt['type']==DriverAsyncEvent.RESULT]
        self.assertTrue(len(test_results) == 1)
        self.assertEqual(test_results[0]['value']['success'], 'Passed')



###############################################################################
#                            QUALIFICATION TESTS                              #
# Device specific qualification tests are for doing final testing of ion      #
# integration.  The generally aren't used for instrument debugging and should #
# be tackled after all unit and integration tests are complete                #
###############################################################################
@attr('QUAL', group='mi')
class DriverQualificationTest(InstrumentDriverQualificationTestCase):
    def setUp(self):
        InstrumentDriverQualificationTestCase.setUp(self)

    def test_direct_access_telnet_mode(self):
        """
        @brief This test manually tests that the Instrument Driver properly supports direct access to the physical instrument. (telnet mode)
        """
        self.assert_direct_access_start_telnet()
        self.assertTrue(self.tcp_client)

        ###
        #   Add instrument specific code here.
        ###

        self.assert_direct_access_stop_telnet()


    def test_poll(self):
        '''
        No polling for a single sample
        '''


    def test_autosample(self):
        '''
        start and stop autosample and verify data particle
        '''


    def test_get_set_parameters(self):
        '''
        verify that all parameters can be get set properly, this includes
        ensuring that read only parameters fail on set.
        '''
        self.assert_enter_command_mode()


    def test_get_capabilities(self):
        """
        @brief Walk through all driver protocol states and verify capabilities
        returned by get_current_capabilities
        """
        self.assert_enter_command_mode()
