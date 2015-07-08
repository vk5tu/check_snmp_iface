#!/usr/bin/python

from __future__ import print_function
import sys

"""Become a Nagios plugin.

This module:

 - ensures (by API design) that the exit code and status text are
   consistent.

 - handles the peculiar intermingling of performance and status data.

 - insists upon a short status (by API design).

 - allows optional long statuses, as a list of strings.

 - allows optional performance data. This is simply a list of strings,
   There is no helper function to assemble those. A description of the
   PerfParse format is at in Section 2.6 of Monitoring Plugins
   Development Guidelines at
     https://www.monitoring-plugins.org/doc/guidelines.html#AEN200

Usage:

  import nagios
  n = nagios.Nagios()
  n.ok('All is well', longtext=['positive', 'news'])

"""

# Copyright (C) AARNet Pty Ltd (ACN 084 540 518), 2015.
# Australia's Academic & Research Network, <http://www.aarnet.edu.au/>
# Written by Glen Turner.

__version__ = "$Id:$"
__copyright__ = "Copyright (C) AARNet Pty Ltd (ACN 084 540 518), 2015."
__license__ = "non-free"
__author__ = "Glen Turner <glen.turner@aarnet.edu.au>"
__credits__ = [ "Australia's Academic and Research Network, www.aarnet.edu.au" ]
__email__= "AARNet network operations <noc@aarnet.edu.au>"
__maintainer__ = "AARNet network operations <noc@aarnet.edu.au>"
__status__ = "Development"


# Nagios plugin API documented at
# <http://nagios.sourceforge.net/docs/3_0/pluginapi.html> and
# <http://nagiosplug.sourceforge.net/developer-guidelines.html>.
# The API defines exit codes and the format of lines printed to stdout.
class Nagios:
    """
    Exit Python with printing and return codes to suit being a Nagios plugin.
    """

    def _printnagios(self,
                     severity,
                     code,
                     shorttext,
                     longtext,
                     perfdata):

        # The specification of the output format at
        #   http://nagios.sourceforge.net/docs/3_0/pluginapi.html
        # says:
        #   TEXT OUTPUT | OPTIONAL PERFDATA
        #   LONG TEXT LINE 1
        #   LONG TEXT LINE 2
        #   ...
        #   LONG TEXT LINE N | PERFDATA LINE 2
        #   PERFDATA LINE 3
        #   ...
        #   PERFDATA LINE N
        # See that webpage for illustrative examples.

        # Line 1 contains severity text, status, some optional perfdata
        print('{}: {}'.format(severity, shorttext), end='')
        if perfdata:
            print(' | {}'.format(perfdata.pop(0)), end='')

        # Next lines contain optional long statuses
        for t in longtext:
            print()
            print(t, end='')

        # Last line of long status is followed by remaining perfdata
        if perfdata:
            print(' | ', end='')
            for p in perfdata:
                print(p)
        else:
            print()

        # Exit with code matching severity
        sys.exit(code)


    def unknown(self, shorttext, longtext=[], perfdata=[]):
        """
        Exit Python returning UNKNOWN status to Nagios.

        Arguments:
        1 -- short text giving status information.
        longtext -- list of strings of further status information.
        perfdata -- list of strings of performance data, although
                    quite how that perfdata was obtained in the
                    UNKNOWN condition is an open question.
        """
        self._printnagios('UNKNOWN',
                          3,
                          shorttext,
                          longtext,
                          perfdata)


    def critical(self, shorttext, longtext=[], perfdata=[]):
        """
        Exit Python returning CRITICAL status to Nagios.

        Arguments:
        1 -- short text giving status information.
        longtext -- list of strings of further status information.
        perfdata -- list of strings of performance data
        """
        self._printnagios('CRITICAL',
                          2,
                          shorttext,
                          longtext,
                          perfdata)


    def warning(self, shorttext, longtext=[], perfdata=[]):
        """
        Exit Python returning WARNING status to Nagios.

        Arguments:
        1 -- short text giving status information.
        longtext -- list of strings of further status information.
        perfdata -- list of strings of performance data
        """
        self._printnagios('WARNING',
                          1,
                          shorttext,
                          longtext,
                          perfdata)


    def ok(self, shorttext, longtext=[], perfdata=[]):
        """
        Exit Python returning OK status to Nagios.

        Arguments:
        1 -- short text giving status information.
        longtext -- list of strings of further status information.
        perfdata -- list of strings of performance data
        """
        self._printnagios('OK',
                          0,
                          shorttext,
                          longtext,
                          perfdata)


    def __init__(self):
        """
        Exit Python to suit being a Nagios plugin.
        """
