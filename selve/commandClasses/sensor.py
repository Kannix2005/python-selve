from multiprocessing import Event
from selve.device import Device
from selve.communication import Command, CommandSingle
from selve.protocol import CommunicationType, DeviceClass, ScanState, SensorState, TeachState, lightDigital, rainDigital, tempDigital, windDigital
from selve.protocol import ParameterType
from selve.commands import CommeoSensorCommand
from selve.utils import singlemask
from selve.utils import true_in_list
from selve.utils import b64bytes_to_bitlist
import logging

_LOGGER = logging.getLogger(__name__)

 
class CommeoSensorTeachStart(Command):
    def __init__(self):
        super().__init__(CommeoSensorCommand.TEACHSTART)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
class CommeoSensorTeachStop(Command):
    def __init__(self):
        super().__init__(CommeoSensorCommand.TEACHSTOP)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
class CommeoSensorTeachResult(Command):
    def __init__(self):
        super().__init__(CommeoSensorCommand.TEACHRESULT)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.teachState = TeachState(int(methodResponse.parameters[0][1]))
        self.timeLeft = int(methodResponse.parameters[1][1])
        self.foundId = int(methodResponse.parameters[2][1])

class CommeoSensorGetIDs(Command):
    def __init__(self):
        super().__init__(CommeoSensorCommand.GETIDS)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.ids = [ b for b in true_in_list(b64bytes_to_bitlist(methodResponse.parameters[0][1]))]
        _LOGGER.debug(self.ids)

class CommeoSensorGetInfo(Command):
    def __init__(self):
        super().__init__(CommeoSensorCommand.GETINFO)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.name = methodResponse.parameters[0][1]
        self.rfAddress = methodResponse.parameters[2][1]

class CommeoSensorGetValues(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoSensorCommand.GETVALUES, deviceId)


    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.windDigital = windDigital(int(methodResponse.parameters[1][1]))
        self.rainDigital = rainDigital(int(methodResponse.parameters[2][1]))
        self.tempDigital = tempDigital(int(methodResponse.parameters[3][1]))
        self.lightDigital = lightDigital(int(methodResponse.parameters[4][1]))
        self.sensorState = SensorState(int(methodResponse.parameters[5][1]))
        self.tempAnalog = int(methodResponse.parameters[6][1])
        self.windAnalog = int(methodResponse.parameters[7][1])
        self.sun1Analog = int(methodResponse.parameters[8][1])
        self.dayLightAnalog = int(methodResponse.parameters[9][1])
        self.sun2Analog = int(methodResponse.parameters[10][1])
        self.sun3Analog = int(methodResponse.parameters[11][1])
        

class CommeoSensorSetLabel(Command):
    def __init__(self, deviceId, name):
        super().__init__(CommeoSensorCommand.SETLABEL, [(ParameterType.INT, deviceId), (ParameterType.STRING, name)])

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSensorDelete(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoSensorCommand.DELETE, deviceId)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSensorWriteManual(Command):
    def __init__(self, deviceId, address, name):
        super().__init__(CommeoSensorCommand.WRITEMANUAL, [(ParameterType.INT, deviceId), (ParameterType.INT, address), (ParameterType.STRING, name)])
    
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class SensorDevice(Device):
    def __init__(self, gateway, id):
        super().__init__(gateway, id)
        self.communicationType = CommunicationType.COMMEO
        self.deviceClass = DeviceClass.SENSOR

    def discover_properties(self):
        try:
            command = CommeoSensorGetInfo(self.ID)
            command.execute(self.gateway)
            self.device_type = command.deviceType
            self.name = command.name if command.name else ""
            self.rfAddress = command.rfAddress
            self.state = command.state
            self.deviceClass = DeviceClass.SENSOR
            self.communicationType = CommunicationType.COMMEO
        except Exception as e1:
            _LOGGER.exception ("not : " + str(e1))


    def scanSensors(self):
        commandStart = CommeoSensorTeachStart()
        commandStop = CommeoSensorTeachStop()
        commandResult = CommeoSensorTeachResult()

        commandStart.execute(self.gateway)
        commandResult.execute(self.gateway)
        while commandResult.timeLeft > 0:
            Event.wait(commandResult.timeLeft+1)
            commandResult.execute(self.gateway)
        if commandResult.scanState == ScanState.END_SUCCESS:
            if commandResult.foundId != -1:
                return commandResult.foundId

    def getSensorValues(self, id):
        command = CommeoSensorGetValues(id)
        command.execute(self.gateway)
        return command

    def setSensorLabel(self, id, label):
        command = CommeoSensorSetLabel(id, label)
        command.execute(self.gateway)

    def deleteSensor(self, id):
        command = CommeoSensorDelete(id)
        command.execute(self.gateway)

    def setSensorManual(self, id, address, name):
        command = CommeoSensorWriteManual(id, address, name)
        command.execute(self.gateway)
