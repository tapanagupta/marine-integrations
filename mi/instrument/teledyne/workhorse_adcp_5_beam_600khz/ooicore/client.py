#!/usr/bin/env python

"""
@package mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.client
@file    mi/instrument/teledyne/workhorse_adcp_5_beam_600khz/ooicore/client.py
@author Carlos Rueda

@brief VADCP instrument client module.
"""

__author__ = 'Carlos Rueda'
__license__ = 'Apache 2.0'

import time
sleep = time.sleep

import socket
import sys

from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.defs import \
    EOLN, DEFAULT_GENERIC_TIMEOUT, State, TimeoutException, MetadataSections
from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.util import \
    connect_socket, prefix
from mi.instrument.teledyne.workhorse_adcp_5_beam_600khz.ooicore.receiver import \
    ReceiverBuilder

import logging
from mi.core.mi_logger import mi_logger as log


class VadcpClient(object):
    """
    A basic client to the instrument.
    """

    def __init__(self, conn_config, outfile=None, prefix_state=True):
        """
        Creates a VadcpClient instance.

        @param conn_config connection configuration
        @param outfile
        @param prefix_state

        """
        self._conn_config = conn_config
        self._outfile = outfile
        self._prefix_state = prefix_state
        self._sock = None
        self._rt = None  # receiver thread

        """sleep time used just before sending data"""
        self._delay_before_send = 0.2

        """generic timeout for various operations"""
        self._generic_timeout = DEFAULT_GENERIC_TIMEOUT

        log.info("VADCP client object created.")

    def set_data_listener(self, data_listener):
        """
        """
        self._data_listener = data_listener

    def set_generic_timeout(self, timeout):
        """Sets generic timeout for various operations.
           By default DEFAULT_GENERIC_TIMEOUT."""
        self._generic_timeout = timeout
        log.info("Generic timeout set to: %d" % self.generic_timeout)

    @property
    def generic_timeout(self):
        """Generic timeout for various operations.
           By default DEFAULT_GENERIC_TIMEOUT."""
        return self._generic_timeout

    def init_comms(self, callback=None):
        """
        Just calls self.connect()
        @param callback ignored.
        """
        self.connect()

    def connect(self):
        """
        Establishes the connection and starts the receiving thread.

        @throws socket.error The socket.error that was raised during the
                         last attempt to connect the socket.
        """
        assert self._sock is None

        host = self._conn_config['four_beam']['address']
        port = self._conn_config['four_beam']['port']

        self._sock = connect_socket(host, port)

        log.info("creating _Receiver")
        self._rt = ReceiverBuilder.build_receiver(self._sock,
                                  outfile=self._outfile,
                                  data_listener=self._data_listener,
                                  prefix_state=self._prefix_state)
        log.info("starting _Receiver")
        self._rt.start()

    def stop_comms(self):
        """
        Just calls self.end()
        """
        self.end()

    def end(self):
        """
        Ends the client.
        """
        if self._sock is None:
            log.warn("end() called again")
            return

        log.info("closing connection")
        try:
            if self._rt:
                self._rt.end()
#            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
#            log.info("socket shutdown and closed")
            log.info("socket closed")
        finally:
            self._sock = None

    def get_current_state(self, timeout=None):
        """
        """
        return self._rt.state

    def _send(self, s, info=None):
        """
        Sends a string. Returns the number of bytes written.

        @param s the string to send
        @param info string for logging purposes
        """
        c = self._sock.send(s)
        if log.isEnabledFor(logging.INFO):
            info_str = (' (%s)' % info) if info else ''
            log.info("_send:%s%s" % (repr(s), info_str))
        return c

    def send(self, string, info=None):
        """
        Sleeps for self._delay_before_send and then sends string + '\r\n'
        """
        self._rt.reset_internal_info()
        sleep(self._delay_before_send)
        s = string.rstrip() + EOLN
        self._send(s, info)

    def send_and_expect_prompt(self, string, timeout=None):
        """
        Sends a string and expects the prompt.
        @param string the string to send
        @param timeout Timeout for the wait, self.generic_timeout by default.

        @retval lines captured from the send to the prompt excluding the
                   prompt.
        @throws TimeoutException if cannot get to the expected state.
        """

        self.send(string)
        sleep(1)
        timeout = timeout or self._generic_timeout
        time_limit = time.time() + timeout
        while self._rt.state != State.PROMPT and time.time() <= \
                                                          time_limit:
            sleep(0.4)
            time_limit = self._rt.recv_time + timeout

        if self._rt.state != State.PROMPT:
            raise TimeoutException(
                    timeout, expected_state=State.PROMPT,
                    curr_state=self._rt.state, lines=self._rt.lines)

        lines = self._rt.lines[0: -1]
        return lines

    def _get_prompt(self, attempts=5):
        """
        Send linefeeds until getting prompt
        """
        # timeout for each attempt
        timeout = 1
        last_exc = None
        for a in xrange(attempts):
            log.info("_get_prompt: attempt=%d" % (a + 1))
            try:
                r = self.send_and_expect_prompt("", timeout)
                return r  # got it
            except TimeoutException, e:
                last_exc = e

        raise last_exc

    def get_latest_ensemble(self, timeout=None):
        """
        CE - Retrieve Most Recent Data Ensemble
        """
        self._get_prompt()
        timeout = timeout or self._generic_timeout
        # now prepare to receive response for latest ensemble
        self._rt.set_latest_pd0(None)
        self.send("CE")
        sleep(0.2)
        time_limit = time.time() + timeout
        while not self._rt.latest_pd0 and time.time() <= time_limit:
            sleep(0.4)
            time_limit = self._rt.recv_time + timeout

        if not self._rt.latest_pd0:
            raise TimeoutException(timeout, msg="waiting for ensemble")

        return self._rt.latest_pd0

    def get_metadata(self, sections=None, timeout=None):
        """
        Gets metadata
        """
        self._get_prompt()
        timeout = timeout or self._generic_timeout

        if not sections:
            sections = MetadataSections.list()

        result = {}
        for name, cmd in sections:
            lines = self.send_and_expect_prompt(cmd, timeout)
            result[name] = "\n".join(lines)

        return result

    def run_recorder_tests(self, timeout=None):
        """
        RB - Recorder Built-In Test
        """
        self._get_prompt()
        timeout = timeout or self._generic_timeout

        lines = self.send_and_expect_prompt("RB", timeout)

        return "\n".join(lines)

    def run_all_tests(self, timeout=None):
        """
        PT200 - All tests
        """
        self._get_prompt()
        timeout = timeout or self._generic_timeout

        lines = self.send_and_expect_prompt("PT200", timeout)

        return "\n".join(lines)

    def start_autosample(self, timeout=None):
        """
        PD0 - Binary output data format
        CS - Start pinging
        """

        timeout = timeout or self._generic_timeout

        # TODO eventually keep current state with enough reliability to
        # check whether we are already in streaming mode ...
#        if self._rt.state == State.COLLECTING_DATA:
#            return  # already streaming
        # ... to just return if already streaming.

        # However, for the moment, force a break:
        self.send_break(timeout=timeout)
        # and continue with regular steps to start autosampling:

        self._get_prompt()

        # send PD0 - Binary output data format
        self.send_and_expect_prompt("PD0", timeout)

        # send CS - Start pinging
        self.send("CS")
        sleep(1)
        time_limit = time.time() + timeout
        while self._rt.state != State.COLLECTING_DATA and time.time() <= \
                                                          time_limit:
            sleep(0.4)
            time_limit = self._rt.recv_time + timeout

        if self._rt.state != State.COLLECTING_DATA:
            raise TimeoutException(
                    timeout, expected_state=State.COLLECTING_DATA,
                    curr_state=self._rt.state, lines=self._rt.lines)

    def stop_autosample(self, timeout=None):
        """
        Sends a "break" command via the OOI Digi connection
        """

        if self._rt.state != State.COLLECTING_DATA:
            return  # not streaming

        timeout = timeout or self._generic_timeout

        self.send_break(timeout=timeout)
        self._get_prompt()

    ###############################################
    # OOI Digi
    ###############################################

    def _connect_ooi_digi(self):
        """
        Establishes the connection to the OOI digi
        """

        host = self._conn_config['ooi_digi']['address']
        port = self._conn_config['ooi_digi']['port']

        sock = connect_socket(host, port)

        outfile = open('vadcp_ooi_digi_output.txt', 'a')
        log.info("creating OOI Digi _Receiver")
        rt = ReceiverBuilder.build_receiver(sock, outfile=outfile)
        log.info("starting OOI Digi _Receiver")
        rt.start()

        return (sock, rt)

    def send_break(self, duration=1000, attempts=3, timeout=None):
        """
        Issues a "break <duration>" command to the OOI digi.

        @param duration Duration for the break command (by default 1000)
        @param attempts Max number of attempts, 3 by default.
        @param timeout

        @retval True iff the command has had effect.
        """

        timeout = timeout or self._generic_timeout

        # TODO the expectation below should be getting the corresponding
        # response on the regular raw port.

        sock, rt = self._connect_ooi_digi()
        ok = False
        try:
            for a in xrange(attempts):
                time.sleep(1)
                rt.reset_internal_info()
                log.info("Sending break (attempt=%d)" % (a + 1))
                sock.send("break %s%s" % (duration, EOLN))
                time.sleep(2)
                response = "\n".join(rt.lines)
                ok = response.find("Sending Serial Break") >= 0
                if ok:
                    break
        finally:
            log.info("ending OOI Digi receiver")
            rt.end()
            time.sleep(2)

            sock.close()
            log.info("socket to OOI Digi closed")

        return ok


def main(host, port, outfile):
    """
    Demo program:
    """

    def user_loop(client):
        """
        Sends lines received from stdin to the socket. EOF and "q" break the
        loop.
        """
        while True:
            cmd = sys.stdin.readline()
            if not cmd or cmd.strip() == "q":
                break
            else:
                client.send(cmd)


    client = VadcpClient(host, port, outfile)
    try:
        client.connect()
        user_loop(client)

#        pd0 = client.get_latest_ensemble()
#        print "get_latest_ensemble=%s" % str(pd0)
    finally:
        print ":: bye"
        client.end()


if __name__ == '__main__':
    usage = """
    USAGE: client.py [options]
       --host address      # instrument address (localhost)
       --port port         # instrument port (required)
       --outfile filename  # file to save all received data
       --loglevel level    # used to eval mi_logger.setLevel(logging.%%s)
    """
    usage += """
    Example:
        client.py --host 10.180.80.178 --port 2101 --outfile vadcp_output.txt
    """

    host = 'localhost'
    port = None
    outfile = None

    arg = 1
    while arg < len(sys.argv):
        if sys.argv[arg] == "--host":
            arg += 1
            host = sys.argv[arg]
        elif sys.argv[arg] == "--port":
            arg += 1
            port = int(sys.argv[arg])
        elif sys.argv[arg] == "--outfile":
            arg += 1
            outfile = file(sys.argv[arg], 'w')
        elif sys.argv[arg] == "--loglevel":
            arg += 1
            loglevel = sys.argv[arg].upper()
            mi_logger = logging.getLogger('mi_logger')
            eval("mi_logger.setLevel(logging.%s)" % loglevel)
        else:
            print "error: unrecognized option %s" % sys.argv[arg]
            port = None
            break
        arg += 1

    if port is None:
        print usage
    else:
        main(host, port, outfile)
