from multiprocessing import Event
from selve.communication import Command, CommandSingle
from selve.protocol import CommunicationType, DeviceClass, ScanState, TeachState, senderEvents
from selve.protocol import ParameterType
from selve.commands import CommeoSenderCommand
from selve.utils import true_in_list
from selve.utils import b64bytes_to_bitlist
from selve.device import Device
import logging
_LOGGER = logging.getLogger(__name__)


class CommeoSenderTeachStart(Command):
    def __init__(self):
        super().__init__(CommeoSenderCommand.TEACHSTART)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoSenderTeachStop(Command):
    def __init__(self):
        super().__init__(CommeoSenderCommand.TEACHSTOP)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
        
class CommeoSenderTeachResult(Command):
    def __init__(self):
        super().__init__(CommeoSenderCommand.TEACHRESULT)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.name = str(methodResponse.parameters[0][1])
        self.teachState = TeachState(int(methodResponse.parameters[1][1]))
        self.timeLeft = int(methodResponse.parameters[1][1])
        self.senderId = int(methodResponse.parameters[2][1])
        self.senderEvent = senderEvents(int(methodResponse.parameters[3][1]))

class CommeoSenderGetIDs(Command):
    def __init__(self):
        super().__init__(CommeoSenderCommand.GETIDS)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.ids = [ b for b in true_in_list(b64bytes_to_bitlist(methodResponse.parameters[0][1]))]
        _LOGGER.debug(self.ids)
        
class CommeoSenderGetInfo(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoSenderCommand.GETINFO, deviceId)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.name = methodResponse.parameters[0][1] if methodResponse.parameters[0][1] else ""
        self.rfAddress = methodResponse.parameters[2][1]
        self.rfChannel = int(methodResponse.parameters[3][1])
        self.rfResetCount = int(methodResponse.parameters[4][1])

class CommeoSenderGetValues(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoSenderCommand.GETVALUES, deviceId)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.lastEvent = senderEvents(int(methodResponse.parameters[1][1]))
        
class CommeoSenderSetLabel(Command):
    def __init__(self, deviceId, name):
        super().__init__(CommeoSenderCommand.SETLABEL, [(ParameterType.INT, deviceId), (ParameterType.STRING, name)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
        
class CommeoSenderDelete(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoSenderCommand.DELETE, deviceId)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
        
class CommeoSenderWriteManual(Command):
    def __init__(self, deviceId, rfAddress, rfChannel, rfResetCount, name):
        super().__init__(CommeoSenderCommand.WRITEMANUAL, [(ParameterType.INT, deviceId), (ParameterType.INT, rfAddress), (ParameterType.INT, rfChannel), (ParameterType.INT, rfResetCount), (ParameterType.STRING, name)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
        
class SenderDevice(Device):
    def __init__(self, gateway, id):
        super().__init__(gateway, id)
        self.communicationType = CommunicationType.COMMEO
        self.deviceClass = DeviceClass.SENDER

    def discover_properties(self):
        try:
            command = CommeoSenderGetInfo(self.ID)
            command.execute(self.gateway)
            self.device_type = command.deviceType
            self.name = command.name
            self.rfAddress = command.rfAddress
            self.state = command.state
            self.deviceClass = DeviceClass.SENDER
            self.communicationType = CommunicationType.COMMEO
        except Exception as e1:
            _LOGGER.exception ("not : " + str(e1))


    def scanSender(self):
        commandStart = CommeoSenderTeachStart()
        commandStop = CommeoSenderTeachStop()
        commandResult = CommeoSenderTeachResult()

        commandStart.execute(self.gateway)
        commandResult.execute(self.gateway)
        while commandResult.timeLeft > 0:
            Event.wait(commandResult.timeLeft+1)
            commandResult.execute(self.gateway)
        if commandResult.scanState == ScanState.END_SUCCESS:
            if commandResult.foundId != -1:
                return commandResult.foundId
                
    def getDeviceValues(self, id):
        command = CommeoSenderGetValues(id)
        command.execute(self.gateway)
        return command

    def setDeviceLabel(self, id, label):
        command = CommeoSenderSetLabel(id, label)
        command.execute(self.gateway)

    def deleteDevice(self, id):
        command = CommeoSenderDelete(id)
        command.execute(self.gateway)

    def setDeviceManual(self, id, address, channel, resetCount, name):
        command = CommeoSenderWriteManual(id, address, channel, resetCount, name)
        command.execute(self.gateway)
