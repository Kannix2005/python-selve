from selve.commandClasses.sender import CommeoSenderGetInfo
from selve.device import Device
from selve.communication import Command, CommandSingle
from selve.protocol import CommunicationType, DeviceClass, DeviceType, lightDigital, rainDigital, tempDigital, windDigital
from selve.protocol import ParameterType
from selve.commands import CommeoSenSimCommand
from selve.utils import true_in_list
from selve.utils import b64bytes_to_bitlist
import logging


_LOGGER = logging.getLogger(__name__)


class CommeoSenSimStore(Command):
    def __init__(self, deviceId, senSimId):
        super().__init__(CommeoSenSimCommand.STORE, [(ParameterType.INT, senSimId), (ParameterType.INT, deviceId)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
class CommeoSenSimDelete(Command):
    def __init__(self, deviceId, senSimId):
        super().__init__(CommeoSenSimCommand.DELETE, [(ParameterType.INT, senSimId), (ParameterType.INT, deviceId)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
class CommeoSenSimGetConfig(Command):
    def __init__(self, senSimId):
        super().__init__(CommeoSenSimCommand.GETCONFIG, [(ParameterType.INT, senSimId)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.name = str(methodResponse.parameters[0][1])
        self.senSimId = int(methodResponse.parameters[1][1])
        self.activity = bool(methodResponse.parameters[2][1])

class CommeoSenSimSetConfig(Command):
    def __init__(self, senSimId, activate):
        super().__init__(CommeoSenSimCommand.SETCONFIG, [(ParameterType.INT, senSimId), (ParameterType.INT, activate)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSenSimSetLabel(Command):
    def __init__(self, senSimId, name):
        super().__init__(CommeoSenSimCommand.SETLABEL, [(ParameterType.INT, senSimId), (ParameterType.INT, name)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSenSimSetValues(Command):
    def __init__(self, senSimId, windDigital, rainDigital, tempDigital, lightDigital, tempAnalog, windAnalog, sun1Analog, dayLightAnalog, sun2Analog, sun3Analog):
        super().__init__(CommeoSenSimCommand.SETVALUES, [(ParameterType.INT, senSimId), (ParameterType.INT, windDigital), (ParameterType.INT, rainDigital), (ParameterType.INT, tempDigital), (ParameterType.INT, lightDigital), (ParameterType.INT, tempAnalog), (ParameterType.INT, windAnalog), (ParameterType.INT, sun1Analog), (ParameterType.INT, dayLightAnalog), (ParameterType.INT, sun2Analog), (ParameterType.INT, sun3Analog)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSenSimGetValues(CommandSingle):
    def __init__(self, senSimId):
        super().__init__(CommeoSenSimCommand.GETVALUES, senSimId)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.windDigital = windDigital(int(methodResponse.parameters[1][1]))
        self.rainDigital = rainDigital(int(methodResponse.parameters[2][1]))
        self.tempDigital = tempDigital(int(methodResponse.parameters[3][1]))
        self.lightDigital = lightDigital(int(methodResponse.parameters[4][1]))
        self.tempAnalog = int(methodResponse.parameters[5][1])
        self.windAnalog = int(methodResponse.parameters[6][1])
        self.sun1Analog = int(methodResponse.parameters[7][1])
        self.dayLightAnalog = int(methodResponse.parameters[8][1])
        self.sun2Analog = int(methodResponse.parameters[9][1])
        self.sun3Analog = int(methodResponse.parameters[10][1])

class CommeoSenSimGetIDs(Command):
    def __init__(self):
        super().__init__(CommeoSenSimCommand.GETIDS)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.ids = [ b for b in true_in_list(b64bytes_to_bitlist(methodResponse.parameters[0][1]))]
        _LOGGER.debug(self.ids)

class CommeoSenSimFactory(CommandSingle):
    def __init__(self, senSimId):
        super().__init__(CommeoSenSimCommand.FACTORY, senSimId)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSenSimDrive(Command):
    def __init__(self, senSimId, command):
        super().__init__(CommeoSenSimCommand.DRIVE, [(ParameterType.INT, senSimId), (ParameterType.INT, command)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSenSimSetTest(Command):
    def __init__(self, senSimId, testMode):
        super().__init__(CommeoSenSimCommand.SETTEST, [(ParameterType.INT, senSimId), (ParameterType.INT, testMode)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSenSimGetTest(CommandSingle):
    def __init__(self, senSimId):
        super().__init__(CommeoSenSimCommand.GETTEST)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.testMode = bool(methodResponse.parameters[1][1])
    
class SenSimDevice(Device):
    def __init__(self, gateway, id):
        super().__init__(gateway, id)
        self.communicationType = CommunicationType.COMMEO
        self.deviceClass = DeviceClass.SENSIM

    def discover_properties(self):
        try:
            command = CommeoSenderGetInfo(self.ID)
            command.execute(self.gateway)
            self.device_type = DeviceType(0)
            self.name = command.name
            self.rfAddress = command.rfAddress
            self.state = command.state
            self.deviceClass = DeviceClass.SENSIM
            self.communicationType = CommunicationType.COMMEO
        except Exception as e1:
            _LOGGER.exception ("not : " + str(e1))


    def storeSenSim(self, deviceid, sensimid):
        command = CommeoSenSimStore(deviceid, sensimid)
        command.execute(self.gateway)

    def deleteSenSim(self, deviceId, senSimId):
        command = CommeoSenSimDelete(deviceId, senSimId)
        command.execute(self.gateway)

    def getSenSimConfig(self, id):
        command = CommeoSenSimGetConfig(id)
        command.execute(self.gateway)

    def setSenSimConfig(self, id, activity=True):
        command = CommeoSenSimSetConfig(id, activity)
        command.execute(self.gateway)

    def setSenSimLabel(self, id, name):
        command = CommeoSenSimSetLabel(id, name)
        command.execute(self.gateway)

    def setSenSimValues(self, id, values):
        command = CommeoSenSimSetValues(id, values.windDigital, values.rainDigital, values.tempDigital, values.lightDigital, values.tempAnalog, values.windAnalog, values.sun1Analog, values.dayLightAnalog, values.sun2Analog, values.sun2Analog)
        command.execute(self.gateway)

    def getSenSimValues(self, id):
        command = CommeoSenSimGetValues(id)
        command.execute(self.gateway)
        return command

    def resetSenSimToFactory(self, id):
        command = CommeoSenSimFactory(id)
        command.execute(self.gateway)

    def driveSenSim(self, id, commandV):
        command = CommeoSenSimDrive(id, commandV)
        command.execute(self.gateway)

    def setTestSenSimOn(self, id):
        command = CommeoSenSimSetTest(id, 1)
        command.execute(self.gateway)

    def setTestSenSimOff(self, id):
        command = CommeoSenSimSetTest(id, 0)
        command.execute(self.gateway)

    def getTestSenSim(self, id):
        command = CommeoSenSimGetTest(id)
        command.execute(self.gateway)
        return command.testMode
