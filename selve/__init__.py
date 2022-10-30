#!/usr/bin/python

import asyncio
import nest_asyncio
from selve.commandClasses.command import CommeoCommandDevice, CommeoCommandGroup, CommeoCommandGroupMan
from selve.commandClasses.common import CommeoParamGetEvent, CommeoParamSetEvent, CommeoServiceFactoryReset, CommeoServiceGetState, CommeoServiceGetVersion, CommeoServicePing, CommeoServiceReset
from selve.commandClasses.sensor import CommeoSensorGetIDs, SensorDevice
from selve.commandClasses.senSim import CommeoSenSimGetIDs, SenSimDevice
from selve.commandClasses.sender import CommeoSenderGetIDs, SenderDevice
from selve.commandClasses.group import CommeoGroupGetIDs, GroupDevice
from selve.commandClasses.actor import ActorDevice, CommeoDeviceGetIDs, CommeoDeviceSave, CommeoDeviceScanResult, CommeoDeviceScanStart, CommeoDeviceScanStop
from selve.commandClasses.iveo import IveoCommandGetIds, IveoDevice
from selve.protocol import DeviceCommandTypes, ScanState, ServiceState, process_response
from selve.communication import incomingEvent

import time
import serial
import logging
import threading
import queue

_LOGGER = logging.getLogger(__name__)
nest_asyncio.apply()

class Gateway():   

    def __init__(self, port, discover = True):
        """                
        Arguments:
            port {String} -- Serial port string as it is used in pyserial
        
        Keyword Arguments:
            discover {bool} -- True if the gateway should try to discover 
                               the devices on init (default: {True})
        """
        self.port = port
        self.connected = False
        self.inputQueue = queue.Queue()
        self.outputQueue = queue.Queue()
        self._LOGGER = _LOGGER
        self.lock = threading.Lock()
        self.devices: dict = {}
        
        
        self.configserial()

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # no event loop running:
            loop = asyncio.new_event_loop()

        if discover:
            _LOGGER.info("Discovering devices")
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.discover())

        #self.readThread = threading.Thread(target=self.readFromPort)
        #self.readThread.start()

        #self.writeThread = threading.Thread(target=self.writePort)
        #self.writeThread.start()
    
    def configserial(self):
        """
        Configure the serial port
        """
        self.ser = serial.Serial(
            port=self.port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS)
        self.ser.timeout = 0
        self.ser.xonxoff = False
        self.ser.rtscts = False
        self.ser.dsrdtr = False
        self.ser.writeTimeout = 2

    def handleData(self, data):
        incomingEvent(str(data))

    def readFromPort(self):
        while True:
            response_str = "" 
            with self.lock: 
                if not self.ser.isOpen():
                    self.ser.open()
                if self.ser.inWaiting() > 0:                        
                    response_str = "" 
                    while True:
                        response = self.ser.readline().strip()
                        response_str += response.decode()
                        if (response.decode() == ''):
                            break
                        
                    _LOGGER.debug('read data: ' + response_str)
                    self.ser.close()
                    return process_response(response_str) 
                    ## inform callback of events

                
    def writePort(self):
        while True:
            response_str = "" 
            with self.lock:
                if not self.outputQueue.empty():     
                    if not self.ser.isOpen():
                        self.ser.open()
                    try:
                        #self.ser.flushInput()
                        #self.ser.flushOutput()
                        
                        self.ser.write(self.outputQueue.get())
                        self.ser.flush()
                        #time.sleep(0.5)
                        response_str = "" 
                        while True:
                            response = self.ser.readline().strip()
                            response_str += response.decode()
                            if (response.decode() == ''):
                                break
                            
                        self.ser.close()
                        _LOGGER.info('read data: ' + response_str)
                        #return process_response(response_str)
                        # handle response somehow here
                    except Exception as e1:
                        _LOGGER.exception ("error communicating...: " + str(e1))
        

    async def executeCommand(self, command):
        """[summary]
        Execute the given command using the serial port.
        It opens a communication to the serial port each time a
        command is executed.
        At this moment it doesn't keep a queue of commands. If
        a command blocks the serial it will wait.
        
        Arguments:
            command {protocol.MethodCall} -- Command to be send 
            through the serial port
        
        Returns:
            MethodResponse -- if the command was executed 
            sucessufully
            ErrorResponse -- if the gateway returns an error
        """
        with self.lock:
            commandstr = command.serializeToXML()
            _LOGGER.info('Gateway writting: ' + str(commandstr))

            try:
                if not self.ser.isOpen():
                    self.ser.open()
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                
                self.ser.write(commandstr)
                time.sleep(0.5)
                response_str = "" 
                while True:
                    response = self.ser.readline().strip()
                    response_str += response.decode()
                    if (response.decode() == ''):
                        break
                    
                _LOGGER.debug('read data: ' + response_str)            
                self.ser.close()
                return process_response(response_str)
                        
            except Exception as e:
                _LOGGER.error ("error communicating: " + str(e))

            self.ser.close()
            return None

    async def discover(self):
        """[summary]
            Discover all devices registered on the usb-commeo        
        """
        await self.gatewayReady()
            

        commandIveo = IveoCommandGetIds()
        commandCommeoActors = CommeoDeviceGetIDs()
        commandCommeoGroups = CommeoGroupGetIDs()
        commandCommeoSenders = CommeoSenderGetIDs()
        commandCommeoSenSims = CommeoSenSimGetIDs()
        commandCommeoSensors = CommeoSensorGetIDs()
        num_retries = 3
        retry_n = 0
        retry_m = 0
        while not hasattr(commandIveo, "ids") and retry_n <=num_retries:
            await commandIveo.execute(self)
            retry_n += 1
            time.sleep(1)
        retry_n = 0
        retry_m = 0
        while not hasattr(commandCommeoActors, "ids") and retry_m <=num_retries:
            await commandCommeoActors.execute(self)
            retry_m += 1
            time.sleep(1)
        retry_n = 0
        retry_m = 0
        while not hasattr(commandCommeoGroups, "ids") and retry_m <=num_retries:
            await commandCommeoGroups.execute(self)
            retry_m += 1
            time.sleep(1)
        retry_n = 0
        retry_m = 0
        while not hasattr(commandCommeoSenders, "ids") and retry_m <=num_retries:
            await commandCommeoSenders.execute(self)
            retry_m += 1
            time.sleep(1)
        retry_n = 0
        retry_m = 0
        while not hasattr(commandCommeoSenSims, "ids") and retry_m <=num_retries:
            await commandCommeoSenSims.execute(self)
            retry_m += 1
            time.sleep(1)
        retry_n = 0
        retry_m = 0
        while not hasattr(commandCommeoSensors, "ids") and retry_m <=num_retries:
            await commandCommeoSensors.execute(self)
            retry_m += 1
            time.sleep(1)


        self.devices = {}
        if not hasattr(commandIveo, "ids"):
            _LOGGER.info("Associated Iveo Devices not found") 
            iveoDevices = {}
        else:
            _LOGGER.debug(f'discover ids: {commandIveo.ids}')
            iveoDevices = dict([(id, IveoDevice(self, id) )for id in commandIveo.ids])
        
        if not hasattr(commandCommeoActors, "ids"):
            _LOGGER.info("Associated Commeo Devices not found") 
            commeoActors = {}
        else:
            _LOGGER.debug(f'discover ids: {commandCommeoActors.ids}')
            commeoActors = dict([(id, ActorDevice(self, id) )for id in commandCommeoActors.ids])
        
        if not hasattr(commandCommeoGroups, "ids"):
            _LOGGER.info("Associated Commeo Groups not found") 
            commeoGroups = {}
        else:
            _LOGGER.debug(f'discover ids: {commandCommeoGroups.ids}')
            commeoGroups = dict([(id, GroupDevice(self, id) )for id in commandCommeoGroups.ids])
        
        if not hasattr(commandCommeoSenders, "ids"):
            _LOGGER.info("Associated Commeo Devices not found") 
            commeoSenders = {}
        else:
            _LOGGER.debug(f'discover ids: {commandCommeoSenders.ids}')
            commeoSenders = dict([(id, SenderDevice(self, id) )for id in commandCommeoSenders.ids])
        
        if not hasattr(commandCommeoSenSims, "ids"):
            _LOGGER.info("Associated Commeo Devices not found") 
            commeoSenSims = {}
        else:
            _LOGGER.debug(f'discover ids: {commandCommeoSenSims.ids}')
            commeoSenSims = dict([(id, SenSimDevice(self, id) )for id in commandCommeoSenSims.ids])
        
        if not hasattr(commandCommeoSensors, "ids"):
            _LOGGER.info("Associated Commeo Devices not found") 
            commeoSensors = {}
        else:
            _LOGGER.debug(f'discover ids: {commandCommeoSensors.ids}')
            commeoSensors = dict([(id, SensorDevice(self, id) )for id in commandCommeoSensors.ids])
        

        self.devices.update(iveoDevices) 
        self.devices.update(commeoActors) 
        self.devices.update(commeoGroups) 
        self.devices.update(commeoSenders) 
        self.devices.update(commeoSenSims) 
        self.devices.update(commeoSensors)
        
        for id, device in self.devices.items():
            await device.discover_properties()
        
        self.list_devices() 
       
    def addDevice(self, id, device):
        self.devices = self.devices.update({id:device})

    def deleteDevice(self, id):
        if self.is_id_registered(id):
            del self.devices[id]

    def is_id_registered(self, id):
        """[summary]
        check if a device id is registered on the gateway
        Arguments:
            id {int} -- Device id to check
        
        Returns:
            boolean -- True if the id is registered
                       False otherwise
        """
        return id in self.devices
        
    def findFreeId(self):
        i = 0
        while i < 64:
            if not self.is_id_registered(i):
                return i
            i=i+1

    def list_devices(self):
        """[summary]
        Print the list of registered devices
        """ 
        for id, device in self.devices.items():
            #print(str(device))
            _LOGGER.info(str(device))
           
    ## Common ##
    async def pingGateway(self):
        self.gatewayReady()
        command = CommeoServicePing()
        await command.execute(self)
        print("Ping")

    # GATEWAY STATE....

    async def gatewayState(self):
        command = CommeoServiceGetState()
        await command.execute(self)
        if hasattr(command, "status"):
            return command.status

    async def gatewayReady(self):
        state = await self.gatewayState() 
        if state == ServiceState.READY:
            return
        else:
            raise GatewayError

    async def getVersionG(self):
        self.gatewayReady()
        command = CommeoServiceGetVersion()
        return await command.execute(self)

    async def getGatewayFirmwareVersion(self):
        command = self.getVersionG()
        if hasattr(command, "version"):
            return command.version

    async def getGatewaySerial(self):
        command = self.getVersionG()
        if hasattr(command, "serial"):
            return command.serial

    async def getGatewaySpec(self):
        command = self.getVersionG()
        if hasattr(command, "spec"):
            return command.spec

    async def resetGateway(self):
        self.gatewayReady()
        command = CommeoServiceReset()
        await command.execute(self)
        while not command.executed:
            time.sleep(1)
        command = CommeoServiceGetState()
        await command.execute(self)
        retries = 0
        while command.status != ServiceState.READY:
            retries = retries+1
            await command.execute(self)
            if retries == 5:
                break
            time.sleep(3)
        if command.status != ServiceState.READY:
            _LOGGER.info("Error: Gateway could not be reset or loads too long")
        else:
            _LOGGER.info("Gateway reset")

    async def factoryResetGateway(self):
        self.gatewayReady()
        command = CommeoServiceFactoryReset()
        await command.execute(self)
        if command.executed:
            _LOGGER.info("Factory reset successful")
        else:
            _LOGGER.info("Factory reset failed")

    async def setEvents(self, eventDevice, eventSensor, eventSender, eventLogging, eventDuty):
        self.gatewayReady()
        command = CommeoParamSetEvent(eventDevice, eventSensor, eventSender, eventLogging, eventDuty)
        command.execute(self)

    async def getEvents(self):
        self.gatewayReady()
        command = CommeoParamGetEvent()
        await command.execute(self)
        _LOGGER.debug("Events: " + str(command.eventDevice) + " " + str(command.eventSensor) + " " + str(command.eventSender) + " " + str(command.eventLogging) + " " + str(command.eventDuty))

## Actor

    async def sendCommandToActor(self, id, command, type=DeviceCommandTypes.MANUAL, parameter=0):
        self.gatewayReady()
        command = CommeoCommandDevice(id, command, type, parameter)
        await command.execute(self)
        return command.executed

    async def scanActorDevices(self):
        self.gatewayReady()
        commandStart = CommeoDeviceScanStart()
        commandStop = CommeoDeviceScanStop()
        commandResult = CommeoDeviceScanResult()

        await commandStart.execute(self)
        await commandResult.execute(self)
        while commandResult.scanState == ScanState.RUN or commandResult.scanState == ScanState.VERIFY:
            await commandResult.execute(self)
            time.sleep(1)
        if commandResult.scanState == ScanState.END_SUCCESS:
            if commandResult.noNewDevices > 0:
                return commandResult.foundIds

        return {}

    async def saveActorDevices(self, ids):
        self.gatewayReady()
        if len(ids) > 0:
            for id in ids:
                commandSave = CommeoDeviceSave(id)
                await commandSave.execute(self)
                dev = ActorDevice(self, id , True)
                self.addDevice(id, dev)
                dev.saveDevice()

    async def deleteActorDevice(self, id):
        if self.is_id_registered(id):
            dev:ActorDevice = self.devices[id]
            dev.deleteDevice()

## Group

    async def sendCommandToGroup(self, id, command, type=DeviceCommandTypes.MANUAL, parameter=0):
        self.gatewayReady()
        command = CommeoCommandGroup(id, command, type, parameter)
        await command.execute(self)
        return command.executed

    async def sendCommandToGroupMan(self, idMask, command, type=DeviceCommandTypes.MANUAL, parameter=0):
        self.gatewayReady()
        command = CommeoCommandGroupMan(command, type, idMask, parameter)
        await command.execute(self)
        return command.ids


class GatewayError(Exception):
    pass
