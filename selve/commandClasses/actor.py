import asyncio
from enum import Enum
from selve import commands
from selve import utils
from selve.commandClasses.command import CommeoCommandDevice

from selve.protocol import CommandType, CommunicationType, DayMode, DeviceClass, DeviceCommandTypes, DeviceState, MethodCall, MovementState, ScanState, ServiceState
from selve.protocol import ParameterType
from selve.protocol import DeviceType
from selve.commands import Commands, CommeoCommandCommand, CommeoDeviceCommand, CommeoEventCommand, CommeoGroupCommand, CommeoParamCommand, CommeoSenSimCommand, CommeoSenderCommand, CommeoSensorCommand, CommeoServiceCommand
from selve.utils import intToBoolarray, singlemask, valueToPercentage
from selve.utils import true_in_list
from selve.utils import b64bytes_to_bitlist
from selve.communication import Command, CommandSingle
from selve.device import Device
import logging
_LOGGER = logging.getLogger(__name__)



class CommeoDeviceScanStart(Command):
    def __init__(self):
        super().__init__(CommeoDeviceCommand.SCANSTART)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
class CommeoDeviceScanStop(Command):
    def __init__(self):
        super().__init__(CommeoDeviceCommand.SCANSTOP)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
class CommeoDeviceScanResult(Command):
    def __init__(self):
        super().__init__(CommeoDeviceCommand.SCANRESULT)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.scanState = ScanState(int(methodResponse.parameters[0][1]))
        self.noNewDevices = int(methodResponse.parameters[1][1])
        self.foundIds = [ b for b in true_in_list(b64bytes_to_bitlist(methodResponse.parameters[2][1]))]

class CommeoDeviceSave(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoDeviceCommand.SAVE, deviceId)
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoDeviceGetIDs(Command):
    def __init__(self):
        super().__init__(CommeoDeviceCommand.GETIDS)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.ids = [ b for b in true_in_list(b64bytes_to_bitlist(methodResponse.parameters[0][1]))]
        _LOGGER.debug(self.ids)

class CommeoDeviceGetInfo(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoDeviceCommand.GETINFO, deviceId)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.name = methodResponse.parameters[0][1]
        self.rfAddress = methodResponse.parameters[2][1]
        self.deviceType = DeviceType(int(methodResponse.parameters[3][1]))
        self.state = DeviceState(int(methodResponse.parameters[4][1]))

class CommeoDeviceGetValues(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoDeviceCommand.GETVALUES, deviceId)


    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.name = methodResponse.parameters[0][1] if methodResponse.parameters[0][1] else ""
        self.movementState = MovementState(int(methodResponse.parameters[2][1]))
        self.value = valueToPercentage(int(methodResponse.parameters[3][1]))
        self.targetValue = valueToPercentage(int(methodResponse.parameters[4][1]))

        bArr = intToBoolarray(int(methodResponse.parameters[5][1]))
        self.unreachable = bArr[0]
        self.overload = bArr[1]
        self.obstructed = bArr[2]
        self.alarm = bArr[3]
        self.lostSensor = bArr[4]
        self.automaticMode = bArr[5]
        self.gatewayNotLearned = bArr[6]
        self.windAlarm = bArr[7]
        self.rainAlarm = bArr[8]
        self.freezingAlarm = bArr[9]
        
        self.dayMode = DayMode(int(methodResponse.parameters[6][1]))

class CommeoDeviceSetFunction(Command):
    def __init__(self, deviceId, function):
        super().__init__(CommeoDeviceCommand.SETFUNCTION, [(ParameterType.INT, deviceId), (ParameterType.INT, function)])

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoDeviceSetLabel(Command):
    def __init__(self, deviceId, name):
        super().__init__(CommeoDeviceCommand.SETLABEL, [(ParameterType.INT, deviceId), (ParameterType.STRING, name)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoDeviceSetType(Command):
    def __init__(self, deviceId, type):
        super().__init__(CommeoDeviceCommand.SETTYPE, [(ParameterType.INT, deviceId), (ParameterType.INT, type.value)])
    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])

class CommeoDeviceDelete(CommandSingle):
    def __init__(self, deviceId):
        super().__init__(CommeoDeviceCommand.DELETE, deviceId)

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])
    
class CommeoDeviceWriteManual(Command):
    def __init__(self, deviceId, rfAddress, name, deviceType):
        super().__init__(CommeoDeviceCommand.WRITEMANUAL, [(ParameterType.STRING, name), (ParameterType.INT, deviceId), (ParameterType.INT, rfAddress), (ParameterType.INT, deviceType.value)])

    def process_response(self, methodResponse):
        super().process_response(methodResponse)
        self.executed = bool(methodResponse.parameters[0][1])


class ActorDevice(Device):
    def __init__(self, gateway, id):
        super().__init__(gateway, id)
        self.communicationType = CommunicationType.COMMEO
        self.deviceClass = DeviceClass.ACTOR

    async def discover_properties(self):
        try:
            command = CommeoDeviceGetInfo(self.ID)
            await command.execute(self.gateway)
            self.device_type = command.deviceType
            self.name = command.name
            self.rfAddress = command.rfAddress
            self.state = command.state
        except Exception as e1:
            _LOGGER.exception ("not : " + str(e1))

    
    async def getDeviceValues(self):
        command = CommeoDeviceGetValues(self.ID)
        await command.execute(self.gateway)
        
        self.name = command.name
        self.movementState = command.movementState
        self.value = command.value
        self.targetValue = command.targetValue
        self.unreachable = command.unreachable
        self.overload = command.overload
        self.obstructed = command.obstructed
        self.alarm = command.alarm
        self.lostSensor = command.lostSensor
        self.automaticMode = command.automaticMode
        self.gatewayNotLearned = command.gatewayNotLearned
        self.windAlarm = command.windAlarm
        self.rainAlarm = command.rainAlarm
        self.freezingAlarm = command.freezingAlarm
        self.dayMode = command.dayMode
        return command

    async def setDeviceFunction(self, func):
        command = CommeoDeviceSetFunction(self.ID, func)
        await command.execute(self.gateway)

    async def setDeviceLabel(self):
        command = CommeoDeviceSetLabel(self.ID, self.name)
        await command.execute(self.gateway)

    async def setDeviceType(self):
        command = CommeoDeviceSetType(self.ID, self.device_type)
        await command.execute(self.gateway)

    async def deleteDevice(self):
        command = CommeoDeviceDelete(self.ID)
        await command.execute(self.gateway)
        self.gateway.deleteDevice(self.ID)

    async def setDeviceManual(self):
        command = CommeoDeviceWriteManual(self.ID, self.rfAddress, self.name, self.device_type)
        await command.execute(self.gateway)

    async def executeCommand(self, command, commandType = DeviceCommandTypes.MANUAL, parameter = 0):
        command = CommeoCommandDevice(self.ID, command, commandType, parameter)
        await command.execute(self.gateway)
        return command

    async def stop(self, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        await self.executeCommand(CommandType.STOP, type)

    async def moveDown(self, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        await self.executeCommand(CommandType.DRIVEDOWN, type)
    
    async def moveUp(self, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        await self.executeCommand(CommandType.DRIVEUP, type)
    
    async def moveIntermediatePosition1(self, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        await self.executeCommand(CommandType.DRIVEPOS1, type)

    async def moveIntermediatePosition2(self, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        await self.executeCommand(CommandType.DRIVEPOS2, type)
    
    async def driveToPos(self, position, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        await self.executeCommand(CommandType.DRIVEPOS, type, utils.percentageToValue(position))

    async def stepUp(self, degrees, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        await self.executeCommand(CommandType.STEPUP, type, degrees)

    async def stepDown(self, degrees, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        await self.executeCommand(CommandType.STEPDOWN, type, degrees)

    async def setAutomatic(self, autoOn, forced=False):
        if forced:
            type=DeviceCommandTypes.FORCED
        else:
            type=DeviceCommandTypes.MANUAL

        if autoOn:
            await self.executeCommand(CommandType.AUTOON, type)
        else:
            await self.executeCommand(CommandType.AUTOOFF, type)

    async def saveDevice(self):
        command = CommeoDeviceSave(self.ID)
        await command.execute(self.gateway)
        if command.executed:
            _LOGGER.info("Device saved")
        else:
            _LOGGER.info("Device saving failed")

    async def deleteDevice(self):
        command = CommeoDeviceDelete(self.ID)
        await command.execute(self.gateway)
        if command.executed:
            _LOGGER.info("Device deleted")
        else:
            _LOGGER.info("Device deletion failed")
