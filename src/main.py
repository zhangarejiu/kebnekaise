import sys
import time
import traceback

from multiprocessing import Process
from .functions import *
from .plugins import *          # Appears as unused in PyCharm, but simply ignore that.
from .plugins.sandbox import *  # Appears as unused in PyCharm, but simply ignore that.


def operation(wrapper, olap_only=False):
    """
    A process for each market.
    """

    try:
        tlk.log(spacer, wrapper)
        tlk.log(tlk.Greeting, wrapper)

        auditor = ctrl.Auditor(wrapper)
        database = dbms.Database(wrapper)
        advisor = olap.Advisor(database)
        trader = oltp.Trader(advisor)

        if tlk.setup()['live_mode'].lower() == 'yes':
            if not olap_only:
                trader.probe()
            else:
                while not tlk.halt():
                    advisor.broadway()
                    tlk.wait()
        else:
            auditor.test()

        tlk.log(spacer, wrapper)
        tlk.log('', wrapper)
    except:
        tlk.log(traceback.format_exc(), wrapper)


def control(timeout=3):
    """
    Start a new process for each enabled (authorized) plugin.
    """

    try:
        tlk.log('STARTING UP OPERATIONS... HELLO!')
        tlk.log(tlk.Greeting)

        authorized = tlk.setup()['authorized'].split()
        bots = {Process(target=operation, args=(plg,))
                for plg in tlk.Plugins if plg.Brand in authorized}

        for b in bots:
            b.start()

        while not tlk.halt():
            time.sleep(.1)

        for b in bots:
            b.join(timeout)
        time.sleep(timeout)

        for b in bots:
            b.terminate()
        tlk.halt(remove=True)

        tlk.log('SHUTTING DOWN OPERATIONS... BYE!')
        tlk.log('')
    except:
        tlk.log(traceback.format_exc())


if __name__ == '__main__':
    spacer = '$$$$$ $$$$$ $$$$$ $$$$$ $$$$$ $$$$$ $$$$$'
    tlk = ctrl.Toolkit(sys.argv[1])
    control()
