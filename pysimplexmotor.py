from pymodbus.client.sync import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder

from constants import *


class PySimplexMotor(object):

    def __init__(self, identifier, address, modbus_client):
        """
        Initializes a new motor with a unique identifier, modbus address, and modbus client.
        :param identifier: An identifier to recognize your specific motor.
        :param address: The modbus address of your motor, set using the SimplexMotion tool.
        :param modbus_client: The Pymodbus client designed to communicate with SimplexMotion motors over modbus.
        """
        self.identifier = identifier
        self.address = address
        self.modbus_client = modbus_client
        assert isinstance(identifier, str) and isinstance(address, int) and isinstance(modbus_client, ModbusSerialClient)

    def get_position(self) -> int:
        """
        Gets the current position of the motor. This is found in the current position register.
        :return: An integer value for the current position of the motor
        """
        pos_response = self.modbus_client.read_holding_registers(MOTOR_POS, 2, unit=self.address)
        if pos_response.isError():
            raise Exception('Unable to retrieve current position. {}'.format(pos_response))
        decoder = BinaryPayloadDecoder.fromRegisters(pos_response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
        return decoder.decode_32bit_int()

    def get_speed(self) -> int:
        """
        Gets the current speed of the motor. This is found in the motors speed register.
        :return: An integer value for the current speed of the motor
        """
        speed_response = self.modbus_client.read_holding_registers(MOTOR_SPEED, 1, unit=self.address)
        if speed_response.isError():
            raise Exception('Unable to retrieve current speed. {}'.format(speed_response))
        return speed_response.registers[0]

    def get_torque(self):
        """
        Gets the current torque of the motor. This is found in the motors torque register.
        :return: An integer value for the current torque of the motor
        """
        torque_response = self.modbus_client.read_holding_registers(MOTOR_TORQUE, 1, unit=self.address)
        if torque_response.isError():
            raise Exception('Unable to retrieve current torque. {}'.format(torque_response))
        return torque_response.registers[0]

    def get_acceleration(self):
        """
        Gets the current acceleration of the motor. This is found in the motor max acceleration register.
        :return: An integer value for the maximum acceleration of the motor
        """
        acc_response = self.modbus_client.read_holding_registers(MOTOR_RAMP_ACC, 1, unit=self.address)
        if acc_response.isError():
            raise Exception('Unable to retrieve current acceleration. {}'.format(acc_response))
        return acc_response.registers[0]

    def get_current_target(self):
        """
        Gets the current target input on the target register.
        :return: An integer value for the current target input to the motor target register
        """
        target_response = self.modbus_client.read_holding_registers(SET_MOTOR_TARGET, 2, unit=self.address)
        if target_response.isError():
            raise Exception('Unable to retrieve current target. {}'.format(target_response))
        decoder = BinaryPayloadDecoder.fromRegisters(target_response.registers, byteorder=Endian.Big, wordorder=Endian.Big)
        return decoder.decode_32bit_int()

    def get_max_speed(self):
        """
        Gets the maximum speed cap on the motor.
        :return: An integer value for the maximum speed cap set on the motor
        """
        speed_response = self.modbus_client.read_holding_registers(MOTOR_MAX_SPEED, 1, unit=self.address)
        if speed_response.isError():
            raise Exception('Unable to retrieve max speed. {}'.format(speed_response))
        return speed_response.registers[0]

    def get_max_torque(self):
        """
        Gets the maximum torque cap on the motor
        :return: An integer value for the maximum torque cap set on the motor
        """
        torque_response = self.modbus_client.read_holding_registers(MOTOR_MAX_TORQUE, 1, unit=self.address)
        if torque_response.isError():
            raise Exception('Unable to retrieve current torque. {}'.format(torque_response))
        return torque_response.registers[0]

    def get_max_acceleration(self):
        """
        Gets the maximum acceleration cap on the motor
        :return: An integer value for the maximum acceleration cap set on the motor
        """
        acc_response = self.modbus_client.read_holding_registers(MOTOR_MAX_ACCELERATION, 1, unit=self.address)
        if acc_response.isError():
            raise Exception('Unable to retrieve max acceleration. {}'.format(acc_response))
        return acc_response.registers[0]

    def get_mode(self):
        """
        Gets the current mode setting of the motor
        :return: An integer describing the various modes of operation for the motor
        """
        mode = self.modbus_client.read_holding_registers(MODE, 1, unit=self.address)
        if mode.isError():
            raise Exception('Unable to retrieve current mode. {}'.format(mode))
        return mode.registers[0]

    def go_with_speed(self, speed_units, acc_units):
        """
        Rotates the motor with a target speed, and acceleration
        :param speed_units: Units of speed measured in SMUnits. Please use the converter class to convert from RPM.
        :param acc_units: Units of acceleration measured in SMUnits. Please use the converter class to convert from RPM/s
        :return:
        """
        # Check if speed mode, else set to speed and reset target
        read_mode = self.get_mode()
        if read_mode != 33:
            reset = self.reset_motor()
            if not reset:
                raise Exception('Unable to reset motor. {}'.format(reset))
            self.set_mode(33)
        self.set_max_acceleration(acc_units)
        return self.set_target(speed_units)

    def go_to_position(self, steps, speed_units, acc_units):
        """
        Rotates the motor with a target position, at a set speed, and acceleration
        :param steps: Units of position measured in steps. Please use the converter class to convert from steps to meters.
        :param speed_units: Units of speed measured in SMUnits. Please use the converter class to convert from RPM.
        :param acc_units: Units of acceleration measured in SMUnits. Please use the converter class to convert from RPM/s
        :return:
        """
        # Check if position mode, else set to position and reset target
        read_mode = self.get_mode()
        if read_mode != 21:
            reset = self.reset_motor()
            if not reset:
                raise Exception('Unable to reset motor. {}'.format(reset))
            self.set_mode(21)
        self.set_max_speed(speed_units)
        self.set_max_acceleration(acc_units)
        return self.set_target(steps)

    def set_max_speed(self, sm_units) -> bool:
        """
        Sets the maximum speed for a motor
        :param sm_units: Units of speed measured in SMunits. Please use the converter class to convert from RPM to steps.
        :return: Boolean indicating if the write was successful
        """
        write_response = self.modbus_client.write_register(MOTOR_MAX_SPEED, sm_units, unit=self.address)
        return not write_response.isError()

    def set_max_torque(self, torque) -> bool:
        """
        Sets the maximum torque for the motor
        :param torque: Units of torque measured in mNm
        :return: Boolean indicating if the write was successful
        """
        write_response = self.modbus_client.write_register(MOTOR_MAX_TORQUE, torque, unit=self.address)
        return not write_response.isError()

    def set_max_acceleration(self, steps):
        """
        Sets the maximum acceleration for the motor
        :param steps: Units of acceleration measured in SMunits. Please use the converter class to convert from RPM/s to steps.
        :return: Boolean indicating if the write was successful
        """
        write_response = self.modbus_client.write_register(MOTOR_MAX_ACCELERATION, steps, unit=self.address)
        return not write_response.isError()

    def set_max_deceleration(self, steps):
        """
        Sets the maximum deceleration for the motor
        :param steps: Units of acceleration measured in SMunits. Please use the converter class to convert from RPM/s to steps.
        :return: Boolean indicating if the write was successful
        """
        write_response = self.modbus_client.write_register(MOTOR_MAX_DECELERATION, steps, unit=self.address)
        return not write_response.isError()

    def set_mode(self, mode):
        """
        Sets the motor operating mode
        :param mode: Integer indicating the intended operating mode. Consult the simplexmotion manual for details
        :return: Boolean indicating if the write was successful
        """
        write_response = self.modbus_client.write_register(MODE, mode, unit=self.address)
        return not write_response.isError()

    def set_target(self, target):
        """
        Sets the target for the motor
        :param target: Units of acceleration measured in SMunits. Please use the converter class to convert from desired units to steps.
        :return: Boolean indicating if the write was successful
        """
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.add_32bit_int(target)
        request = self.modbus_client.write_registers(SET_MOTOR_TARGET, builder.to_registers(), unit=self.address)
        return not request.isError()

    def reset_motor(self):
        """
        Resets the motor
        :return: Boolean indicating if the write was successful
        """
        write_response = self.modbus_client.write_register(MODE, 1, unit=self.address)
        return not write_response.isError()

    def stop_motor(self):
        """
        Stops the motor
        :return: Boolean indicating if the write was successful
        """
        write_response = self.modbus_client.write_register(MODE, 5, unit=self.address)
        return not write_response.isError()

    def get_current_status(self):
        """
        Gets the current status of the motor, including running data, operating data, and error data.
        :return: A dictionary containing the current data of the motor. Please use the converter class to convert each value into the appropriate unit.
        """
        motor_running_data = self.modbus_client.read_holding_registers(MOTOR_POS, 4, unit=self.address)
        motor_voltage_data = self.modbus_client.read_holding_registers(MOTOR_VOLTAGE, 1, unit=self.address)
        motor_current_data = self.modbus_client.read_holding_registers(TORQUE_CURRENT, 1, unit=self.address)
        motor_operating_data = self.modbus_client.read_holding_registers(TEMP_ELECTRONICS, 2, unit=self.address)
        motor_error_data = self.modbus_client.read_holding_registers(ERROR, 1, unit=self.address)
        if motor_running_data.isError() or motor_error_data.isError() or motor_voltage_data.isError() or motor_current_data.isError() or motor_operating_data.isError():
            raise Exception('Unable to get motor data. {}'.format(motor_running_data, motor_operating_data, motor_current_data, motor_voltage_data, motor_error_data))
        decoder = BinaryPayloadDecoder.fromRegisters(motor_running_data.registers[0:2], byteorder=Endian.Big,
                                                     wordorder=Endian.Big)
        decoder2 = BinaryPayloadDecoder.fromRegisters(motor_voltage_data.registers, byteorder=Endian.Big,
                                                     wordorder=Endian.Big)
        decoder3 = BinaryPayloadDecoder.fromRegisters(motor_current_data.registers, byteorder=Endian.Big,
                                                     wordorder=Endian.Big)
        decoder4 = BinaryPayloadDecoder.fromRegisters(motor_running_data.registers[3:4], byteorder=Endian.Big,
                                                      wordorder=Endian.Big)
        error = motor_error_data.registers[0]

        if error == 0:
            error = "No error"
        if error == 1:
            error = "General internal error"
        if error == 2:
            error = "Internal software timing error"
        if error == 3:
            error = "Error in application: code not terminating"
        if error == 4097:
            error = "General communication error"
        if error == 4098:
            error = "Invalid register error"
        if error == 4353:
            error = "Modbus parity error"
        if error == 4354:
            error = "Modbus framing error"
        if error == 4355:
            error = "Modbus overrun error"
        if error == 4356:
            error = "Modbus checksum error"
        if error == 4357:
            error = "Modbus illegal function code error"
        if error == 4358:
            error = "Modbus illegal diagnostics function code error"
        if error == 8193:
            error = "Hardware overcurrent protection triggered"
        if error == 12289:
            error = "Supply voltage too low"
        if error == 12290:
            error = "Supply voltage too high"
        if error == 16385:
            error = "Temperature of electronics is too high"
        if error == 16386:
            error = "Temperature of motor winding is too high"
        if error == 20481:
            error = "Torque limiting is active"
        if error == 24577:
            error = "Locked shaft condition detected"
        if error == 28673:
            error = "Regulator error is large"

        # TIP: You can get true current drawn by the motor, by multiplying the torque value, and it's corresponding
        # speed.
        return {
            "position": decoder.decode_32bit_int(),
            "speed": motor_running_data.registers[2],
            "torque": decoder4.decode_16bit_int(),
            "voltage": decoder2.decode_16bit_int(),
            "current": decoder3.decode_16bit_int(),
            "electronics_temp": motor_operating_data.registers[0],
            "motor_temp": motor_operating_data.registers[1],
            "error": error
        }

