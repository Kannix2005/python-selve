Python control of selve devices through USB-RF Gateway
======================================================

|PyPI version|

A simple Python API for controlling RF Blinds / shutters / awning from selve using a USB-RF Gateway.
All devices according to the specification are supported. Also integrated are two Threads which monitor an in- and output queue.
If you want to send an async command, just use the writeQueue. readQueue momentarily only reads events from the serial port and does not process them (tbd).


The complete protocol specification can be found at `selve <https://www.selve.de/de/service/software-updates/service-entwicklungstool-commeo-usb-rf-gateway/>`_

Example of use
--------------

Create a new instance of the gateway:

.. code-block:: python

    gat = Gateway(portname)


portname is the name of the serial port where the usb rf gateway is listed on the os. Please refer to the serial library documentation.

By default the gateway will discover all Iveo devices already registered onto the gateway.

To access them:

.. code-block:: python

    gat.devices()

Will return a list of devices. Those can be Iveo or Commeo devices.

Each device can be controlled by using the already defined commands: stop() moveUp() moveToIntermediatePosition1() and moveToIntermediatePosition2()

The library also allows to send directly commands to the gateway without the need of using the device abstraction just create the command and execute using the gateway:

.. code-block:: python

    command = IveoCommandGetIds()
    command.execute(gat)

Once executed the response is stored in the command instance for later user or just to discard.

.. |PyPI version| image:: https://badge.fury.io/py/python-selve-new.svg
   :target: https://badge.fury.io/py/python-selve-new






