import asyncio
from selve.device import Device

from selve.protocol import CommandTypeIveo, CommunicationType, DeviceClass, MethodCall, RepeaterState
from selve.protocol import ParameterType
from selve.protocol import DeviceType
from selve.commands import IveoCommand
from selve.communication import Command, CommandMask, CommandSingle
from selve.utils import true_in_list
from selve.utils import b64bytes_to_bitlist
import logging


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

    
class IveoCommandSetRepeater(Command):
    def __init__(self, repeaterState):
        super().__init__(IveoCommand.SETREPEATER, [(ParameterType.INT, repeaterState)])

class IveoCommandGetRepeater(Command):
    def __init__(self):
        super().__init__(IveoCommand.GETREPEATER)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.repeaterState = RepeaterState(int(methodResponse.parameters[0][1]))

class IveoCommandFactory(CommandSingle):

    def __init__(self, iveoID):
        super().__init__(IveoCommand.FACTORY, iveoID)

class IveoCommandTeach(CommandSingle):
    def __init__(self, iveoID):
        super().__init__(IveoCommand.TEACH, iveoID)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])   

class IveoCommandLearn(CommandSingle):
    def __init__(self, iveoID):
        super().__init__(IveoCommand.LEARN, iveoID)
    
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1]) 
         
class IveoCommandManual(CommandMask):
    def  __init__(self, mask, command):
        super().__init__(IveoCommand.MANUAL, mask, command)
    
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1]) 

class IveoCommandAutomatic(CommandMask):
    def  __init__(self, mask, command):
        super().__init__(IveoCommand.AUTOMATIC, mask, command)
    
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class IveoCommandResult(MethodCall):
    def __init__(self, command, mask, state):
        super().__init__(IveoCommand.RESULT, [(ParameterType.INT, command), (ParameterType.BASE64, mask), (ParameterType.INT, state)])

class IveoCommandSetLabel(Command):
    def __init__(self, iveoId, label):
        super().__init__(IveoCommand.SETLABEL, [(ParameterType.INT, iveoId), (ParameterType.STRING, label)])

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class IveoCommandSetConfig(Command):
    def __init__(self, iveoId, activity, device_type):
        super().__init__(IveoCommand.SETCONFIG, [(ParameterType.INT, iveoId), (ParameterType.INT, activity), (ParameterType.INT, device_type)])
    
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class IveoCommandGetConfig(CommandSingle):
    def __init__(self, iveoId):
        super().__init__(IveoCommand.GETCONFIG, iveoId)
    
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.name = methodResponse.parameters[0][1]
        self.activity = methodResponse.parameters[2][1]
        self.deviceType = DeviceType(int(methodResponse.parameters[3][1]))

class IveoCommandGetIds(Command):
    def __init__(self):
        super().__init__(IveoCommand.GETIDS)
    
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.ids = [ b for b in true_in_list(b64bytes_to_bitlist(methodResponse.parameters[0][1]))]
        _LOGGER.debug(self.ids)

class IveoDevice(Device):

    def __init__(self, gateway, iveoID):
        super().__init__(gateway, iveoID)
        self.communicationType = CommunicationType.IVEO
        self.deviceClass = DeviceClass.IVEO
    
    async def executeCommand(self, commandType, automatic = False):
        if automatic:
            command = IveoCommandAutomatic(self.mask, commandType)
        else:
            command = IveoCommandManual(self.mask, commandType)
        await command.execute(self.gateway)
        return command

    async def discover_properties(self):
        try:
            command = IveoCommandGetConfig(self.ID)
            await command.execute(self.gateway)
            self.device_type = command.deviceType
            self.name = command.name if command.name else ""
            self.activity = command.activity
        except Exception as e1:
            _LOGGER.exception ("not : " + str(e1))

    async def setRepeaterState(self, state):
        command = IveoCommandSetRepeater(state)
        await command.execute(self.gateway)

    async def getRepeaterState(self):
        command = IveoCommandGetRepeater()
        await command.execute(self.gateway)
        return command

    async def setIveoLabel(self):
        command = IveoCommandSetLabel(self.ID, self.name)
        await command.execute(self.gateway)

    async def setIveoConfig(self):
        command = IveoCommandSetConfig(self.ID, self.activity, self.device_type)
        await command.execute(self.gateway)

    async def getIveoConfig(self):
        command = IveoCommandGetConfig(self.ID)
        await command.execute(self.gateway)
        self.device_type = command.deviceType
        self.name = command.name
        self.activity = command.activity

    async def resetIveoChannel(self):
        command = IveoCommandFactory(self.ID)
        await command.execute(self.gateway)
        self.gateway.deleteDevice(self.ID)

    async def learnIveoChannel(self):
        command = IveoCommandLearn(self.ID)
        await command.execute(self.gateway)

    async def setToLearnMode(self):
        self.learnIveoChannel()        

    async def teachIveoChannel(self, channel):
        command = IveoCommandTeach(channel)
        _LOGGER.info("Trying to teach channel " + str(channel))
        await command.execute(self.gateway)
        if command.hasError:
            _LOGGER.info("Teaching failed for channel " + str(channel))
            return
        if await command.executed:
            _LOGGER.info("Channel " + str(channel) + "successfully taught" )

    async def manualIveoCommand(self, command):
        command = IveoCommandManual(self.mask, command)
        await command.execute(self.gateway)
        return command

    async def automaticIveoCommand(self, command):
        command = IveoCommandAutomatic(self.mask, command)
        await command.execute(self.gateway)
        return command


    async def stop(self):
        await self.automaticIveoCommand(CommandTypeIveo.STOP)

    async def moveDown(self):
        await self.automaticIveoCommand(CommandTypeIveo.DRIVEDOWN)
    
    async def moveUp(self):
        await self.automaticIveoCommand(CommandTypeIveo.DRIVEUP)
    
    async def moveIntermediatePosition1(self):
        await self.manualIveoCommand(CommandTypeIveo.POSITION_1)

    async def moveIntermediatePosition2(self):
        await self.manualIveoCommand(CommandTypeIveo.POSITION_2)
    
    async def deleteDevice(self):
        await self.resetIveoChannel()

    async def saveDevice(self):
        await self.teachIveoChannel(self.ID)